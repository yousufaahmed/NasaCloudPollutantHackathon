"use client";

import { useState, useEffect } from "react";
import { fetchWeatherApi } from "openmeteo";

export default function WeatherWidget(props: {
  latitude: number;
  longitude: number;
}) {
  useEffect(() => {
    async function getWeather() {
      const params = {
        latitude: props.latitude,
        longitude: props.longitude,
        hourly: "temperature_2m",
        current: [
          "temperature_2m",
          "rain",
          "wind_speed_10m",
          "relative_humidity_2m",
          "precipitation",
          "apparent_temperature",
        ],
      };
      const url = "https://api.open-meteo.com/v1/forecast";
      const responses = await fetchWeatherApi(url, params);
      const response = responses[0];

      const current = response.current()!;
      console.log("Current weather:", current);
    }
  }, []);
  return <div></div>;
}
