"use client";
import dynamic from "next/dynamic";
import { useGeolocation } from "@uidotdev/usehooks";
import { useState, useEffect } from "react";

const Map = dynamic(() => import("../map"), {
  loading: () => <p>A map is loading</p>,
  ssr: false,
});

// const airQualityPhases() = {
//   good: [
//     `The air quality in ${area} is excellent and refreshing today.`,
//     `Residents in ${area} are enjoying crisp, clean air with low pollution levels.`,
//     `${area} boasts some of the cleanest air in the region this season.`,
//     `Breathing is easy in ${area} thanks to outstanding air quality conditions.`,
//   ],
//   bad: [
//     `The air quality in ${area} has reached unhealthy levels today.`,
//     `Residents in ${area} should limit outdoor activities due to poor air conditions.`,
//     `${area} is experiencing significantly polluted air with high particulate matter.`,
//     `Air quality warnings have been issued for ${area} as pollution levels soar.`,
//   ],
// };

export default function Dashboard() {
  const state = useGeolocation();
  const [position, setPosition] = useState<[number, number]>([51.505, -0.09]);
  const [zoom] = useState<number>(13);
  const [loading, setLoading] = useState<boolean>(true);
  const [maperror, setMapError] = useState<boolean>(false);
  const [filteredpoints, setFilteredPoints] = useState<
    [number, number, number, Date][]
  >([]);
  const [showAirHeatmap, setShowAirHeatmap] = useState<boolean>(false);
  const [showPopHeatmap, setShowPopHeatmap] = useState<boolean>(false);
  const [sliderValue, setSliderValue] = useState(6);

  const exampleHeatPoints: [number, number, number, Date][] = [
    [51.505, -0, 0.8, new Date("2025-01-01")],
    [51.51, -0.15, 0.5, new Date("2025-06-01")],
    [51.52, -0.2, 0.7, new Date("2025-12-01")],
  ];

  useEffect(() => {
    if (state.loading) {
      setLoading(true);
    }

    if (state.error) {
      setMapError(true);
      setLoading(false);
    }

    if (state.latitude && state.longitude && !state.loading && !state.error) {
      setPosition([state.latitude, state.longitude]);
      setLoading(false);
    }
  }, [state]);

  useEffect(() => {
    const selectedDate = new Date(2025, sliderValue, 1);

    // Calculate date range: 2 months before and after
    const twoMonthsBefore = new Date(selectedDate);
    twoMonthsBefore.setMonth(selectedDate.getMonth() - 2);

    const twoMonthsAfter = new Date(selectedDate);
    twoMonthsAfter.setMonth(selectedDate.getMonth() + 2);

    const filteredPoints = exampleHeatPoints.filter((point) => {
      // Assuming point[3] is a Date object or timestamp
      const pointDate = new Date(point[3]);
      return pointDate >= twoMonthsBefore && pointDate <= twoMonthsAfter;
    });

    setFilteredPoints(filteredPoints);
  }, [sliderValue]);

  return (
    <div className="container mx-auto px-[15%] py-6">
      {loading && <p>Loading... (Please enable permissions)</p>}
      {maperror && <p>Failed to get your location</p>}
      {!loading && !maperror && (
        <Map
          position={position}
          zoom={zoom}
          heatMapData={filteredpoints}
          showHeatmap={showAirHeatmap}
        />
      )}

      <div className="py-4 justify-center flex">
        <input
          type="range"
          min={0}
          max={11}
          value={sliderValue}
          step="1"
          onChange={(e) => setSliderValue(Number(e.target.value))}
          className="range range-primary dark:range-neutral transition-colors duration-700"
        />
      </div>
      <div className="inline-flex gap-4 mb-4 justify-center w-full">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={showAirHeatmap}
            onChange={() => setShowAirHeatmap((v) => !v)}
          />
          Show Air Quality
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={showPopHeatmap}
            onChange={() => setShowPopHeatmap((v) => !v)}
          />
          Show Population Density
        </label>
      </div>
    </div>
  );
}
