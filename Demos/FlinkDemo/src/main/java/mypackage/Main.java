package mypackage;

import mypackage.source.Source;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.functions.MapFunction;
import org.apache.flink.api.common.serialization.SimpleStringEncoder;
import org.apache.flink.cep.CEP;
import org.apache.flink.cep.PatternSelectFunction;
import org.apache.flink.cep.PatternStream;
import org.apache.flink.cep.pattern.Pattern;
import org.apache.flink.cep.pattern.conditions.IterativeCondition;
import org.apache.flink.cep.pattern.conditions.SimpleCondition;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.configuration.MemorySize;
import org.apache.flink.configuration.TaskManagerOptions;
import org.apache.flink.core.fs.Path;
import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.streaming.api.datastream.AllWindowedStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.functions.sink.filesystem.StreamingFileSink;
import org.apache.flink.streaming.api.functions.sink.filesystem.rollingpolicies.DefaultRollingPolicy;
import org.apache.flink.streaming.api.functions.windowing.AllWindowFunction;
import org.apache.flink.streaming.api.functions.windowing.WindowFunction;
import org.apache.flink.streaming.api.windowing.assigners.TumblingProcessingTimeWindows;
import org.apache.flink.streaming.api.windowing.time.Time;
import org.apache.flink.streaming.api.windowing.windows.TimeWindow;
import org.apache.flink.util.Collector;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.Objects;

public class Main {
    private static final Logger LOG = LoggerFactory.getLogger(Main.class);

    public static void main(String[] args) throws Exception {

        //Config
        Configuration config = new Configuration();
        config.set(TaskManagerOptions.CPU_CORES, 4.0);
        config.set(TaskManagerOptions.NUM_TASK_SLOTS, 2);
        config.set(TaskManagerOptions.TASK_HEAP_MEMORY, MemorySize.ofMebiBytes(8192));
        config.set(TaskManagerOptions.TASK_OFF_HEAP_MEMORY, MemorySize.ofMebiBytes(2048));
        config.set(TaskManagerOptions.NETWORK_MEMORY_MIN, MemorySize.ofMebiBytes(512));
        config.set(TaskManagerOptions.NETWORK_MEMORY_MAX, MemorySize.ofMebiBytes(512));
        config.set(TaskManagerOptions.MANAGED_MEMORY_SIZE, MemorySize.ofMebiBytes(1024));

        //Start flink environment
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        //Create datasource, using custom source that receives data from rabbitmq
        //Set parallelism to one to ensure exactly once processing, might slow it down? or affect scalabillity
        DataStream<String> rawStream = env.addSource(new Source()).setParallelism(1);

        //Create a pojo from json string for efficient handling, see Event.java
        ObjectMapper objectMapper = new ObjectMapper();

        //Do research on keyed stream. Not possible with current implementation of
        //The graph. Can enable parallel processing, isnt available at this time due to how we currently
        //use links to connect events.
        DataStream<Event> dataStream = rawStream.map(message -> {
            try {
                return objectMapper.readValue(message, Event.class);
            } catch (Exception e) {
                System.err.println("Failed to parse JSON: " + message + e);
                return null;
            }
        }).filter(Objects::nonNull);



        //What does The watermark do? Specifies that events can arrive out of order by up to x seconds.
        //Wait for events to arrive until x seconds has passed to handle events in the correct order, downside
        //Causes delay.
        //withIdleness makes the stream progress if it is idle for more than a second. Why is this needed?
        dataStream = dataStream.assignTimestampsAndWatermarks(
                WatermarkStrategy.<Event>forBoundedOutOfOrderness(Duration.ofSeconds(1))
                        .withTimestampAssigner((event, timestamp) -> event.getMeta().getTime())
                        .withIdleness(Duration.ofSeconds(1)) // Adjust the duration as needed

        );

        dataStream = dataStream
                .windowAll(TumblingProcessingTimeWindows.of(Time.seconds(1)))
                .apply(new AllWindowFunction<Event, Event, TimeWindow>() {
                    @Override
                    public void apply(TimeWindow window, Iterable<Event> input, Collector<Event> out) throws Exception {
                        for (Event event : input) {
                            out.collect(event);
                        }
                    }
                });

        //First pattern, Link ArtC to FCD with Flow_Context


        //Artifact Published pattern
        //Have three valid orders of events
        //Case 1: FCD1 → ArtC → FCD2 → ArtP
        //Case 2: FCD2 → FCD1 → ArtC → ArtP
        //Case 3: FCD1 → FCD2 → ArtC → ArtP
        //Split to pattern into two and apply them seperately. Could be done with or inside one pattern
        //If flink is selected to move on with then explore that.
        Pattern<Event, ?> artifactPublishedCase1Pattern = Pattern.<Event>begin("FCD1")
                .where(SimpleCondition.of(event -> event.getMeta().getType().equals("EiffelFlowContextDefinedEvent")))
                .followedByAny("ArtC")
                .where(new IterativeCondition<Event>() {
                    @Override
                    public boolean filter(Event event, Context<Event> ctx) throws Exception {
                        if (!event.getMeta().getType().equals("EiffelArtifactCreatedEvent")){
                            return false;
                        }
                        Event fcd1 = ctx.getEventsForPattern("FCD1").iterator().next();
                        return HelpFunctions.linksToEvent(event, fcd1, "CONTEXT_DEFINED");
                    }
                })
                .followedByAny("FCD2") // FCD2 follows ArtC
                .where(SimpleCondition.of(event -> event.getMeta().getType().equals("EiffelFlowContextDefinedEvent")))
                .followedByAny("ArtP")
                .where(new IterativeCondition<Event>() {
                    @Override
                    public boolean filter(Event event, Context<Event> ctx) throws Exception {
                        if (!event.getMeta().getType().equals("EiffelArtifactPublishedEvent")){
                            return false;
                        }
                        Event artC = ctx.getEventsForPattern("ArtC").iterator().next();
                        Event fcd2 = ctx.getEventsForPattern("FCD2").iterator().next();

                        boolean linksToArtC = false;
                        boolean linksToFCD2 = false;

                        for (Event.Link link : event.getLinks()) {
                            if (artC.getMeta().getId().equals(link.getId())) {
                                linksToArtC = true;
                            }
                            if (fcd2.getMeta().getId().equals(link.getId())) {
                                linksToFCD2 = true;
                            }
                        }
                        return linksToArtC && linksToFCD2;
                    }
                }).within(Time.seconds(1));

        //Case 2: FCD2 → FCD1 → ArtC → ArtP
        //Case 3: FCD1 → FCD2 → ArtC → ArtP
        Pattern<Event, ?> artifactPublishedCase2And3Pattern = Pattern.<Event>begin("FCD1")
                .where(SimpleCondition.of(event -> event.getMeta().getType().equals("EiffelFlowContextDefinedEvent")))
                .followedByAny("FCD2")
                .where(SimpleCondition.of(event -> event.getMeta().getType().equals("EiffelFlowContextDefinedEvent")))
                .followedByAny("ArtC") // ArtC links to FCD1
                .where(new IterativeCondition<Event>() {
                    @Override
                    public boolean filter(Event event, Context<Event> ctx) throws Exception {
                        if (!event.getMeta().getType().equals("EiffelArtifactCreatedEvent")){
                            return false;
                        }
                        Event fcd1 = ctx.getEventsForPattern("FCD1").iterator().next();
                        Event fcd2 = ctx.getEventsForPattern("FCD2").iterator().next();
                        boolean linksToFcd1;
                        boolean linksToFcd2;
                        for (Event.Link link : event.getLinks()) {
                            linksToFcd1 = fcd1.getMeta().getId().equals(link.getId());
                            linksToFcd2 = fcd2.getMeta().getId().equals(link.getId());
                            if ((linksToFcd1 || linksToFcd2) && link.getType().equals("CONTEXT_DEFINED")) {
                                return true;
                            }
                        }
                        return false;
                    }
                })
                .followedByAny("ArtP") // ArtP must link to both ArtC & FCD2
                .where(new IterativeCondition<Event>() {
                    @Override
                    public boolean filter(Event event, Context<Event> ctx) throws Exception {
                        if (!event.getMeta().getType().equals("EiffelArtifactPublishedEvent")){
                            return false;
                        }
                        Event artC = ctx.getEventsForPattern("ArtC").iterator().next();
                        Event fcd2 = ctx.getEventsForPattern("FCD2").iterator().next();
                        Event fcd1 = ctx.getEventsForPattern("FCD1").iterator().next();

                        //First check link to artC
                        if (!HelpFunctions.linksToEvent(event, artC, "ARTIFACT")){
                            return false;
                        }
                        //Check that it links the correct fcd
                        boolean artCLinksToFcd1;
                        boolean artClinksToFcd2;
                        for (Event.Link link : event.getLinks()) {
                            artCLinksToFcd1 = HelpFunctions.linksToEvent(artC, fcd1, "CONTEXT_DEFINED");
                            artClinksToFcd2 = HelpFunctions.linksToEvent(artC, fcd2, "CONTEXT_DEFINED");

                            if (artCLinksToFcd1) {
                                if (HelpFunctions.linksToEvent(event, fcd2, "CONTEXT_DEFINED")) {
                                    return true;
                                }
                            } else if (artClinksToFcd2) {
                                if (HelpFunctions.linksToEvent(event, fcd1, "CONTEXT_DEFINED")) {
                                    return true;
                                }
                            }
                        }
                        //Did not link to the correct fcd
                        return false;
                    }
                }).within((Time.seconds(1)));

        //Handles both patterns for Artifact published and then merge the output streams.. Not very pretty.
        //Can be handled by creating larger complex pattern with multiple ors.
        PatternStream<Event> artifactPublishedCase1PatternStream = CEP.pattern(dataStream, artifactPublishedCase1Pattern);
        PatternStream<Event> artifactPublishedCase2And3PatternStream = CEP.pattern(dataStream, artifactPublishedCase2And3Pattern);

        DataStream<String> ArtifactPublishedStream1 = artifactPublishedCase1PatternStream.select(new PatternSelectFunction<Event, String>() {
            @Override
            public String select(Map<String, List<Event>> pattern) throws Exception {
                Event fcd1 = pattern.get("FCD1").get(0);
                Event artC = pattern.get("ArtC").get(0);
                Event fcd2 = pattern.get("FCD2").get(0);
                Event artP = pattern.get("ArtP").get(0);

                return String.format("Detected sequence: FCD1(%s), ArtC(%s), FCD2(%s), ArtP(%s)",
                        fcd1.getMeta().getId(), artC.getMeta().getId(), fcd2.getMeta().getId(), artP.getMeta().getId());
            }
        });

        DataStream<String> ArtifactPublishedStream2 = artifactPublishedCase2And3PatternStream.select(new PatternSelectFunction<Event, String>() {
            @Override
            public String select(Map<String, List<Event>> pattern) throws Exception {
                Event fcd1 = pattern.get("FCD1").get(0);
                Event fcd2 = pattern.get("FCD2").get(0);
                Event artC = pattern.get("ArtC").get(0);
                Event artP = pattern.get("ArtP").get(0);
                return String.format("Detected sequence: FCD1(%s), FCD2(%s), ArtC(%s), ArtP(%s)",
                        fcd1.getMeta().getId(), fcd2.getMeta().getId(), artC.getMeta().getId(), artP.getMeta().getId());
            }
        });

        DataStream<String> mergedStream = ArtifactPublishedStream1.union(ArtifactPublishedStream2);
        mergedStream.print("Found Artifact Published");

        Pattern<Event, ?> artifactCreated = Pattern.<Event>begin("FCD")
                .where(SimpleCondition.of(event -> event.getMeta().getType().equals("EiffelFlowContextDefinedEvent")))
                .followedByAny("ArtC")
                .where(new IterativeCondition<Event>() {
                    @Override
                    public boolean filter(Event event, Context<Event> ctx) throws Exception {
                        //Exit early due to wrong type or missing links
                        if (event.getLinks().isEmpty() || !Objects.equals(event.getMeta().getType(), "EiffelArtifactCreatedEvent")){
                            return false;
                        }
                        //Verify correct link
                        Event previousEvent = ctx.getEventsForPattern("FCD").iterator().next();
                        return HelpFunctions.linksToEvent(event, previousEvent, "CONTEXT_DEFINED");
                    }
                }).within(Time.seconds(1));

        PatternStream<Event> artifactCreatedStream = CEP.pattern(dataStream, artifactCreated);

        DataStream<String> result = artifactCreatedStream.select(
                (PatternSelectFunction<Event, String>) patternMatch -> {
                    Event start = patternMatch.get("FCD").get(0);
                    Event middle = patternMatch.get("ArtC").get(0);

                    return String.format("Detected sequence: FCD(" + start.getMeta().getId() + ") ArtC("+ middle.getMeta().getId() + ")");
                }
        );

        result.print("Found Artifact created");

        // Execute the Flink job
        LOG.warn("Execute program");
        env.execute("Flink RabbitMQ Consumer Job");
    }

}


