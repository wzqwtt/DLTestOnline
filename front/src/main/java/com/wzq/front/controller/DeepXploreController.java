package com.wzq.front.controller;

import com.wzq.front.feign.DeepXploreClient;
import com.wzq.front.webSocket.WebSocketServer;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;
import java.time.Duration;
import java.util.*;

@Slf4j
@RestController
public class DeepXploreController {

    @Autowired
    private DeepXploreClient deepXploreClient;

    @RequestMapping("/DLTestMainPage")
    public String demo() {
        return deepXploreClient.pythonClientMain();
    }

    @ResponseBody
    @RequestMapping("/deepxplore")
    public void deepxplore() {
        // run deepxplore
        deepXploreClient.runDeepXplore();
    }

    @ResponseBody
    @RequestMapping("/kafka")
    public void getKafkaConsumer() {
        // 0、配置信息
        Properties properties = new Properties();

        properties.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, "192.168.10.100:9092");

        properties.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        properties.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());

        String groupId = UUID.randomUUID().toString().replace("-", "").toLowerCase();
        properties.put(ConsumerConfig.GROUP_ID_CONFIG, groupId);
        log.info("消费者组ID: " + groupId);

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
                if ("stop".equals(consumerRecord.key())) {
                    break;
                } else {
                    try {
                        // 发送URL到前端
                        WebSocketServer.sendInfo(consumerRecord.value(), "100");
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                }
            }
        }
    }

    /**
     * 测试websocket方法
     *
     * @param cid
     * @param message
     * @return
     */
    @ResponseBody
    @RequestMapping("/push/{cid}")
    public Map pushToWeb(@PathVariable String cid, String message) {
        HashMap<String, Object> result = new HashMap<>();

        try {
            WebSocketServer.sendInfo(message, cid);
            result.put("code", cid);
            result.put("msg", message);
        } catch (IOException e) {
            e.printStackTrace();
        }

        return result;
    }

}
