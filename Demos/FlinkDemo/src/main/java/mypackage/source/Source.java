package mypackage.source;

import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.ConnectionFactory;
import com.rabbitmq.client.DeliverCallback;
import org.apache.flink.streaming.api.functions.source.SourceFunction;

import java.io.IOException;
import java.util.concurrent.TimeoutException;

//The deprecated Sourcefunction is not as optimized as the new Source.
//Due to not being required to specify bounded or unbounded.
//Will be removed in update 2.0. But implementing it was fairly simple.
public class Source implements SourceFunction<String> {
    private volatile boolean running = true;
    private static final String QUEUE_NAME = "hello";
    private Connection connection;
    private Channel channel;

    @Override
    public void run(SourceContext<String> sourceContext) throws Exception {
        // Set up RabbitMQ connection and channel
        ConnectionFactory factory = new ConnectionFactory();
        factory.setHost("localhost");  // Your RabbitMQ host
        connection = factory.newConnection();
        channel = connection.createChannel();

        // Declare the queue (make sure it exists in RabbitMQ)
        channel.queueDeclare(QUEUE_NAME, false, false, false, null);

        // Message consumer logic
        DeliverCallback deliverCallback = (consumerTag, delivery) -> {
            String message = new String(delivery.getBody(), "UTF-8");
            sourceContext.collect(message);  // Emit the message to Flink's downstream operators
        };

        // Start consuming messages from the queue
        channel.basicConsume(QUEUE_NAME, true, deliverCallback, consumerTag -> {});

        // Keep running until cancellation
        while (running) {
            Thread.sleep(1000);  // Keep the source running, you could enhance with more control
        }
    }

    @Override
    public void cancel() {
        // Properly clean up when the source is cancelled
        running = false;
        try {
            if (channel != null) {
                channel.close();
            }
            if (connection != null) {
                connection.close();
            }
        } catch (IOException e) {
            e.printStackTrace();
        } catch (TimeoutException e) {
            throw new RuntimeException(e);
        }
    }
}
