package com.wzq.front.controller;

import com.wzq.front.feign.DeepXploreClient;
import com.wzq.front.webSocket.WebSocketServer;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

@RestController
public class DeepXploreController {

    @Autowired
    private DeepXploreClient deepXploreClient;

    @RequestMapping("/DLTestMainPage")
    public String demo() {
        return deepXploreClient.pythonClientMain();
    }

    @RequestMapping("/deepxplore")
    public void deepxplore() {
        // run deepxplore
        deepXploreClient.runDeepXplore();
    }

    /**
     * 测试websocket方法
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
