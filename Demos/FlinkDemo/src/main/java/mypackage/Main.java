package mypackage;

//
//import mypackage.source.Source;
//import org.apache.flink.api.common.eventtime.WatermarkStrategy;
//import org.apache.flink.api.common.serialization.SimpleStringSchema;
//import org.apache.flink.cep.CEP;
//import org.apache.flink.cep.PatternFlatSelectFunction;
//import org.apache.flink.cep.PatternSelectFunction;
//import org.apache.flink.cep.PatternStream;
//import org.apache.flink.cep.pattern.Pattern;
//import org.apache.flink.cep.pattern.conditions.IterativeCondition;
//import org.apache.flink.cep.pattern.conditions.SimpleCondition;
//import org.apache.flink.configuration.Configuration;
//import org.apache.flink.configuration.MemorySize;
//import org.apache.flink.configuration.TaskManagerOptions;
//import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.JsonNode;
//import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.ObjectMapper;
//import org.apache.flink.streaming.api.datastream.KeyedStream;
//import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
//import org.apache.flink.streaming.api.datastream.DataStream;
//import org.apache.flink.formats.json.JsonNodeDeserializationSchema;
//import org.apache.flink.util.Collector;
//import org.slf4j.Logger;
//import org.slf4j.LoggerFactory;
//
//import java.time.Duration;
//import java.util.List;
//import java.util.Map;
//import java.util.Objects;
//
//public class Main {
//    private static final Logger LOG = LoggerFactory.getLogger(Main.class);
//
//    public static void main(String[] args) throws Exception {
//
//        //Config
//        Configuration config = new Configuration();
//        config.set(TaskManagerOptions.CPU_CORES, 2.0);
//        config.set(TaskManagerOptions.NUM_TASK_SLOTS, 2);
//        config.set(TaskManagerOptions.TASK_HEAP_MEMORY, MemorySize.ofMebiBytes(1024));
//        config.set(TaskManagerOptions.TASK_OFF_HEAP_MEMORY, MemorySize.ofMebiBytes(512));
//        config.set(TaskManagerOptions.NETWORK_MEMORY_MIN, MemorySize.ofMebiBytes(64));
//        config.set(TaskManagerOptions.NETWORK_MEMORY_MAX, MemorySize.ofMebiBytes(64));
//        config.set(TaskManagerOptions.MANAGED_MEMORY_SIZE, MemorySize.ofMebiBytes(128));
//
//        //Start flink environment
//        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
//
//        //Create datasource, using custom source that receives data from rabbitmq
//        //Set parallelism to one to ensure exactly once processing, might slow it down?
//        DataStream<String> rawStream = env.addSource(new Source()).setParallelism(1);
//
//        //Create a pojo from json string for efficient handling, see Event.java
//        ObjectMapper objectMapper = new ObjectMapper();
//        //Do research on keyed stream. Not possible with current implementation of
//        //The graph. Can enable parallel processing, isnt available at this time?
//        DataStream<Event> dataStream = rawStream.map(message -> {
//            try {
//                return objectMapper.readValue(message, Event.class);
//            } catch (Exception e) {
//                System.err.println("Failed to parse JSON: " + message + e);
//                return null;
//            }
//        }).filter(Objects::nonNull);
//        dataStream.print();
//        //This prob doesnt do anything
//        //dataStream = dataStream.filter(event -> event.getMeta() != null && event.getMeta().getType() != null);
//
//        //What does duration.ofseconds  Specifies that events can arrive out of order by up to 10 seconds.
//        //It is then handled by the watermark strategy
//      dataStream = dataStream.assignTimestampsAndWatermarks(
//                WatermarkStrategy.<Event>forBoundedOutOfOrderness(Duration.ofSeconds(10))
//                        .withTimestampAssigner((event, timestamp) -> event.getTimestamp())
//        );
//
//
//        Pattern<Event, ?> ArtifactCreated = Pattern.<Event>begin("FCD")
//                .where(new IterativeCondition<Event>() {
//                    @Override
//                    public boolean filter(Event event, Context<Event> ctx) throws Exception {
//                        System.out.println("I pattern");
//                        LOG.warn("Checking event: {} with ID: {}", event.getType(), event.getId());
//                        return true; // Keep all events for now
//                    }
//                });
//        //First pattern, Link ArtC to FCD with Flow_Context
//        /*Pattern<Event, ?> ArtifactCreated = Pattern.<Event>begin("FCD")
//                .where(SimpleCondition.of(event -> true));
//                .followedByAny("ArtC")
//                .where(new IterativeCondition<Event>() {
//                    @Override
//                    public boolean filter(Event event, Context<Event> ctx) throws Exception {
//                        //Exit early due to wrong type or missing links
//                        System.out.println("test");
//                        if (event.getLinks().isEmpty() || !Objects.equals(event.getMeta().getType(), "EiffelArtifactCreatedEvent")){
//                            return false;
//                        }
//                        //Check if the new event links to the FCD in this pattern, Does this really need to be a loop?
//                        for (Event previousEvent : ctx.getEventsForPattern("EiffelFlowContextDefinedEvent")) {
//                            for (Event.Link link : event.getLinks()) {
//                                if (previousEvent.getMeta().getId().equals(link.getTarget())){ //&& link.getType().equals("ARTIFACT")) {
//                                    return true;
//                                }
//                            }
//                        }
//                        return false; // No match found
//                    }
//                });*/
//        dataStream
//                .map(event -> event.getType() + event.getId())  // Extract ID as a String
//                .print("Pre pattern Type");
//        //Apply pattern to datastream
//        PatternStream<Event> patternStream = CEP.pattern(dataStream, ArtifactCreated);
//
//        patternStream.flatSelect(new PatternFlatSelectFunction<Event, Object>() {
//            @Override
//            public void flatSelect(Map<String, List<Event>> pattern, Collector<Object> collector) throws Exception {
//                System.out.println("Pattern" + pattern);
//            }
//        });
//
//
//        DataStream<String> result = patternStream.select(
//                (PatternSelectFunction<Event, String>) patternMatch -> {
//                    Event start = patternMatch.get("FCD").get(0);
//                   // Event middle = patternMatch.get("ArtC").get(0);
//
//                    return String.format("Detected sequence:" + start.getType() + start.getId());
//                }
//        );
//
//       /* dataStream
//        .map(event -> event.getMeta().getType())  // Extract ID as a String
//.print("Extracted Type");*/
//        result.print("Found Artifact created");
//
//        //patternStream.print();
//
//
//        // Execute the Flink job
//        LOG.warn("Execute program");
//        env.execute("Flink RabbitMQ Consumer Job");
//    }
//}






import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.cep.CEP;
import mypackage.source.Source;
import org.apache.flink.cep.PatternSelectFunction;
import org.apache.flink.cep.PatternStream;
import org.apache.flink.cep.pattern.Pattern;
import org.apache.flink.cep.pattern.conditions.IterativeCondition;
import org.apache.flink.cep.pattern.conditions.SimpleCondition;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.configuration.MemorySize;
import org.apache.flink.configuration.TaskManagerOptions;
import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.core.ObjectCodec;
import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.datastream.SingleOutputStreamOperator;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.util.Objects;

import java.time.Duration;
import java.util.Map;

public class Main {
    private static final Logger LOG = LoggerFactory.getLogger(Main.class);

    public static void main(String[] args) throws Exception {
        LOG.info("Starting program");

        //Flink Configuration
        Configuration config = new Configuration();
        config.set(TaskManagerOptions.CPU_CORES, 2.0);
        config.set(TaskManagerOptions.NUM_TASK_SLOTS, 2);
        config.set(TaskManagerOptions.TASK_HEAP_MEMORY, MemorySize.ofMebiBytes(1024));
        config.set(TaskManagerOptions.TASK_OFF_HEAP_MEMORY, MemorySize.ofMebiBytes(512));
        config.set(TaskManagerOptions.NETWORK_MEMORY_MIN, MemorySize.ofMebiBytes(64));
        config.set(TaskManagerOptions.NETWORK_MEMORY_MAX, MemorySize.ofMebiBytes(64));
        config.set(TaskManagerOptions.MANAGED_MEMORY_SIZE, MemorySize.ofMebiBytes(128));
        config.setString("rootLogger.level", "WARN");

        // Flink Execution Environment
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        // Event Stream
      /*DataStream<Event> inputEventStream = env.fromData(
                new Event("1", "click", 1000, new String[]{}),
                new Event("2", "scroll", 2000, new String[]{"1"}),
                new Event("3", "click", 3000, new String[]{"2"}),
                new Event("4", "click", 4000, new String[]{"2"}),
                new Event("5", "purchase", 5000, new String[]{"1", "2"}),
                new Event("6", "scroll", 6000, new String[]{})
        ).assignTimestampsAndWatermarks(
                WatermarkStrategy.<Event>forBoundedOutOfOrderness(Duration.ofSeconds(10))
                        .withTimestampAssigner((event, timestamp) -> event.getTimestamp())
        );*/

        DataStream<String> rawStream = env.addSource(new Source());
        rawStream.print();


        ObjectMapper objectMapper = new ObjectMapper();
        DataStream<Event> inputEventStream = rawStream.map(message -> {
          try {

              return objectMapper.readValue(message, Event.class);
         } catch (Exception e) {
               System.err.println("Failed to parse JSON: " + message + e);
                return null;
          }
      });
        inputEventStream
                .map(event -> event.getType())  // Extract ID as a String
                .print("Extracted Type");
        inputEventStream = inputEventStream.assignTimestampsAndWatermarks(
                WatermarkStrategy.<Event>forBoundedOutOfOrderness(Duration.ofSeconds(10))
                        .withTimestampAssigner((event, timestamp) -> event.getTimestamp())
        );

        inputEventStream.print();
        // Define CEP Pattern
        Pattern<Event, ?> pattern = Pattern.<Event>begin("start")
                .where(SimpleCondition.of(event -> event.getId().equals("1")))  // Event 1 (start)
                .next("middle")
                .where(SimpleCondition.of(event -> event.getId().equals("2")))  // Event 2 (middle)
                .followedBy("end")
                .where(SimpleCondition.of(event -> event.getId().equals("3")));  // Event 3 (end)


        Pattern<Event, ?> matchClickAndScroll = Pattern.<Event>begin("start")
                .where(SimpleCondition.of(event -> event.getType().equals("click"))) // First event must be a click
                .followedByAny("linkedEvent")
                .where(new IterativeCondition<Event>() {
                    @Override
                    public boolean filter(Event event, Context<Event> ctx) throws Exception {
                        System.out.println("New filter call");

                        if (event.getLinks().length == 0){
                            System.out.println("Exit filter early" + event.getId());
                            return false;
                        }
                        //This will one get node use ctx.getEventsForPattern("start")[0]?
                        for (Event previousEvent : ctx.getEventsForPattern("start")) {
                            System.out.println(previousEvent.getId() + " previous event " + event.getId() + " current event");
                            for (String link : event.getLinks()) {         //Do this first to prevent unnecessary iterations
                                if (previousEvent.getId().equals(link) && event.getType().equals("scroll")) {
                                    return true;
                                }
                            }
                        }
                        return false; // No match found
                    }
                });

        // Apply CEP
        PatternStream<Event> patternStream = CEP.pattern(inputEventStream, matchClickAndScroll);


        DataStream<String> result = patternStream.select(
                (PatternSelectFunction<Event, String>) patternMatch -> {
                    Event start = patternMatch.get("start").get(0);
                    Event middle = patternMatch.get("linkedEvent").get(0);

                    return String.format("Detected sequence: [%s -> %s]", start, middle);
                }
        );

        // Print Results
        result.print("Output");

        // Execute Flink Job
        LOG.info("Executing Flink job");
        env.execute("Flink CEP Example");
        LOG.info("Finished program");
    }
}

