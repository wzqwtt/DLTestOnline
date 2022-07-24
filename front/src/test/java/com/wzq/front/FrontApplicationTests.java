package com.wzq.front;

import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

import java.time.Duration;
import java.util.ArrayList;
import java.util.Properties;

@SpringBootTest
class FrontApplicationTests {

    @Test
    void contextLoads() {
        // 0、配置信息
        Properties properties = new Properties();
        properties.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, "192.168.10.100:9092");
        // 反序列化类型
        properties.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        properties.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());

        // 消费者组ID
        properties.put(ConsumerConfig.GROUP_ID_CONFIG, "DLTestDeepXplore");

        // 1、创建消费者对象
        KafkaConsumer<String, String> kafkaConsumer = new KafkaConsumer<>(properties);

        // 2、订阅主题
        ArrayList<String> topics = new ArrayList<>();
        topics.add("deepxplore");
        kafkaConsumer.subscribe(topics);

        // 3、消费
        while (true) {
            ConsumerRecords<String, String> consumerRecords = kafkaConsumer.poll(Duration.ofSeconds(1));
            for (ConsumerRecord<String, String> consumerRecord : consumerRecords) {
                System.out.println("key: " + consumerRecord.key() + " value:" + consumerRecord.value());
            }
        }
    }

}
