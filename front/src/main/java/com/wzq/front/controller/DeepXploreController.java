package com.wzq.front.controller;

import com.wzq.front.feign.DeepXploreClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

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
        deepXploreClient.runDeepXplore();
    }

}
