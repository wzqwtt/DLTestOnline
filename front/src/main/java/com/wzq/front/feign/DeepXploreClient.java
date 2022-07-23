package com.wzq.front.feign;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;

@FeignClient(url = "http://192.168.10.100:5000", name = "DeepXploreClient")
public interface DeepXploreClient {

    @RequestMapping(value = "/", method = RequestMethod.GET, consumes = "application/json")
    String pythonClientMain();

    @RequestMapping(value = "/deepxplore", method = RequestMethod.GET, consumes = "application/json")
    String runDeepXplore();

}
