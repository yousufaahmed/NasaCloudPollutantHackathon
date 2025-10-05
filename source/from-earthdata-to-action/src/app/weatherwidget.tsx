"use client";

import { useState, useEffect } from "react";
import { fetchWeatherApi } from "openmeteo";

type WeatherWidgetProps = {
  latitude: number;
  longitude: number;
};

export default function WeatherWidget(props: WeatherWidgetProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [weatherData, setWeatherData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function getWeather() {
      setLoading(true);
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

      const utcOffsetSeconds = response.utcOffsetSeconds();

      const current = response.current()!;
      const hourly = response.hourly()!;

      const weather = {
        current: {
          time: new Date((Number(current.time()) + utcOffsetSeconds) * 1000),
          temperature_2m: current.variables(0)!.value(),
          rain: current.variables(1)!.value(),
          wind_speed_10m: current.variables(2)!.value(),
          relative_humidity_2m: current.variables(3)!.value(),
          precipitation: current.variables(4)!.value(),
          apparent_temperature: current.variables(5)!.value(),
        },
        hourly: {
          time: [
            ...Array(
              (Number(hourly.timeEnd()) - Number(hourly.time())) /
                hourly.interval()
            ),
          ].map(
            (_, i) =>
              new Date(
                (Number(hourly.time()) +
                  i * hourly.interval() +
                  utcOffsetSeconds) *
                  1000
              )
          ),
          temperature_2m: hourly.variables(0)!.valuesArray(),
        },
      };
      setWeatherData(weather);
      setLoading(false);
    }
    getWeather();
  }, [props.latitude, props.longitude]);

  return (
    <div className="card card-border bg-base-100 ">
      <div className="card-body font-mono text-center text-black dark:text-white transition-colors duration-700">
        <div>
          <svg
            width="10%"
            height="10%"
            viewBox="0 0 24 24"
            fill="none"
            className="justify-center mx-auto mb-2"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M6.5 19C4.01472 19 2 16.9853 2 14.5C2 12.1564 3.79151 10.2313 6.07974 10.0194C6.54781 7.17213 9.02024 5 12 5C14.9798 5 17.4522 7.17213 17.9203 10.0194C20.2085 10.2313 22 12.1564 22 14.5C22 16.9853 19.9853 19 17.5 19C13.1102 19 10.3433 19 6.5 19Z"
              stroke="currentColor"
              strokeWidth="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
          {loading && "Loading weather..."}
          {!loading && weatherData && (
            <>
              <div>
                Temperature:{" "}
                {(
                  Math.round(weatherData.current.temperature_2m * 100) / 100
                ).toFixed(2)}
                °C
              </div>
              <div>Rain: {weatherData.current.rain} mm</div>
              <div>
                Wind Speed:{" "}
                {(
                  Math.round(weatherData.current.wind_speed_10m * 100) / 100
                ).toFixed(2)}{" "}
                km/h
              </div>
              <div>Humidity: {weatherData.current.relative_humidity_2m}%</div>
              <div>Precipitation: {weatherData.current.precipitation} mm</div>
              <div>
                Apparent Temperature:{" "}
                {(
                  Math.round(weatherData.current.apparent_temperature * 100) /
                  100
                ).toFixed(2)}
                °C
              </div>
            </>
          )}
          {!loading && !weatherData && "No weather data available."}
        </div>
      </div>
    </div>
  );
}
