import com.rabbitmq.client.*;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

public class Agency {
    private static final String EXCHANGE_NAME = "exchange";

    public static void main(String[] argv) throws Exception {
        //PRODUCER

        BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(System.in));
        System.out.println("Podaj nazwę agencji: ");
        String agencyName = bufferedReader.readLine();


        ConnectionFactory factory = new ConnectionFactory();
        factory.setHost("localhost");
        Connection connection = factory.newConnection();
        Channel channel = connection.createChannel();

        channel.queueDeclare(agencyName, false, false, false, null);
        System.out.println("created queue: " + agencyName);

        channel.exchangeDeclare(EXCHANGE_NAME, BuiltinExchangeType.DIRECT);

        Consumer consumer = new DefaultConsumer(channel) {
            @Override
            public void handleDelivery(String consumerTag, Envelope envelope, AMQP.BasicProperties properties, byte[] body) throws IOException {
                String message = new String(body, "UTF-8");
                System.out.println("Otrzymano: " + message);
            }
        };
        System.out.println("Oczekiwanie na wiadomości....");
        channel.basicConsume(agencyName, true, consumer);

        while (true) {
            System.out.println("Dostępne usługi: osoby, ladunek, satelita");
            System.out.println("Wybierz usługę: ");
            String message = bufferedReader.readLine();
            System.out.println(message);

            if ("osoby".equals(message)) {
                sendMessage("people", message, channel, agencyName, 1);
            } else if ("ladunek".equals(message)) {
                sendMessage("load", message, channel, agencyName, 2);
            } else if ("satelita".equals(message)) {
                sendMessage("satellite", message, channel, agencyName, 3);
            } else if ("exit".equals(message)) {
                channel.close();
                connection.close();
                break;
            }
        }
    }

    public static void sendMessage(String key, String message, Channel channel, String agencyName, int number) throws IOException, InterruptedException {
        channel.basicPublish(EXCHANGE_NAME, key, null,  (agencyName + ":" + number +message).getBytes(StandardCharsets.UTF_8));
        System.out.println("Send: " + agencyName + ":" + number + ":" + message);
        Thread.sleep(1000);
    }
}
