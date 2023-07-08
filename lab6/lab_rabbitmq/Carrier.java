import com.rabbitmq.client.*;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

public class Carrier {
    private static final String EXCHANGE_NAME = "exchange";

    public static void main(String[] argv) throws Exception {

        ConnectionFactory factory = new ConnectionFactory();
        factory.setHost("localhost");
        Connection connection = factory.newConnection();
        Channel channel = connection.createChannel();

        channel.exchangeDeclare(EXCHANGE_NAME, BuiltinExchangeType.DIRECT);
        channel.basicQos(1);

        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        System.out.println("przewóz osób oraz ładunków wybierz 1");
        System.out.println("przewóz ładunków oraz umieszczenie satelity na orbicie wybierz 2");

        String PEOPLE_QUEUE = "people";
        String LOAD_QUEUE = "load";
        String SATELLITE_QUEUE = "satellite";
        int optionNumber;
        while (true) {
            String input = br.readLine();
            if ("1".equals(input)) {
                createQueue(channel, PEOPLE_QUEUE, PEOPLE_QUEUE);
                createQueue(channel, LOAD_QUEUE, LOAD_QUEUE);
                optionNumber = 1;
                break;
            }
            else if ("2".equals(input)) {
                createQueue(channel, SATELLITE_QUEUE, SATELLITE_QUEUE);
                createQueue(channel, LOAD_QUEUE, LOAD_QUEUE);
                optionNumber = 2;
                break;
            }
        }
        Consumer consumer = new DefaultConsumer(channel) {
            @Override
            public void handleDelivery(String consumerTag, Envelope envelope, AMQP.BasicProperties properties, byte[] body) throws IOException {
                String message = new String(body, "UTF-8");
                System.out.println("Otrzymano: " + message);
                int id = message.indexOf(":");
                String agencyQueue = message.substring(0, id);
                String newMessage = agencyQueue + " -> potwierdzono wykonanie usługi";
                channel.basicPublish("", agencyQueue, null, newMessage.getBytes("UTF-8"));

                System.out.println("Wysłano potwierdzenie: " + newMessage);
            }
        };

        System.out.println("Oczekiwanie na wiadomości...");
        switch (optionNumber){
            case 1: {
                channel.basicConsume(PEOPLE_QUEUE, true, consumer);
                channel.basicConsume(LOAD_QUEUE, true, consumer);
                break;
            }
            case 2:{
                channel.basicConsume(SATELLITE_QUEUE, true, consumer);
                channel.basicConsume(LOAD_QUEUE, true, consumer);
            }
        }
    }
    private static void createQueue(Channel channel,String queueName, String key) throws IOException {
        channel.queueDeclare(queueName, false, false, false, null);
        channel.queueBind(queueName, EXCHANGE_NAME, key);
        System.out.println("stworzono kolejkę: " + queueName);
    }
}
