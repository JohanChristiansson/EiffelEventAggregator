package mypackage;


import mypackage.source.Source;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.datastream.DataStream;

public class Main {

    public static void main(String[] args) throws Exception {
        // Create a streaming execution environment
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        // Create a DataStream using the custom RabbitMQ Source
        DataStream<String> messageStream = env.addSource(new Source());

        // Perform operations on the stream (for example, printing the messages)
        messageStream.print();

        // Execute the Flink job
        env.execute("Flink RabbitMQ Consumer Job");
    }
}

/*import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.cep.CEP;
import org.apache.flink.cep.PatternSelectFunction;
import org.apache.flink.cep.PatternStream;
import org.apache.flink.cep.pattern.Pattern;
import org.apache.flink.cep.pattern.conditions.IterativeCondition;
import org.apache.flink.cep.pattern.conditions.SimpleCondition;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.configuration.MemorySize;
import org.apache.flink.configuration.TaskManagerOptions;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.util.Map;

public class Main {
    private static final Logger LOG = LoggerFactory.getLogger(Main.class);

    public static void main(String[] args) throws Exception {
        LOG.info("Starting program");

        // Flink Configuration
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
        DataStream<Event> inputEventStream = env.fromData(
                new Event("1", "click", 1000L, new String[]{}),
                new Event("2", "scroll", 2000L, new String[]{"1"}),
                new Event("3", "click", 3000L, new String[]{"2"}),
                new Event("4", "click", 4000L, new String[]{"2"}),
                new Event("5", "purchase", 5000L, new String[]{"1", "2"}),
                new Event("6", "scroll", 6000L, new String[]{})
        ).assignTimestampsAndWatermarks(
                WatermarkStrategy.<Event>forBoundedOutOfOrderness(Duration.ofSeconds(10))
                        .withTimestampAssigner((event, timestamp) -> event.getTimestamp())
        );

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
}*/

