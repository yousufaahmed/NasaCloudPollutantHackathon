"use client";
import dynamic from "next/dynamic";
import { useGeolocation } from "@uidotdev/usehooks";
import { useState, useEffect } from "react";

const Map = dynamic(() => import("../map"), {
  loading: () => <p>A map is loading</p>,
  ssr: false,
});

export default function Dashboard() {
  const state = useGeolocation();
  const [position, setPosition] = useState<[number, number]>([51.505, -0.09]);
  const [zoom] = useState<number>(13);
  const [loading, setLoading] = useState<boolean>(true);
  const [maperror, setMapError] = useState<boolean>(false);
  const [sliderValue, setSliderValue] = useState(0);

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

  return (
    <div className="container mx-auto px-[15%] py-6">
      <div className="py-4 justify-center flex">
        <input
          type="range"
          min={0}
          max="100"
          value={sliderValue}
          onChange={(e) => setSliderValue(Number(e.target.value))}
          className="range range-primary dark:range-neutral transition-colors duration-700"
        />
      </div>
      {loading && <p>Loading... (Please enable permissions)</p>}
      {maperror && <p>Failed to get your location</p>}
      {!loading && !maperror && <Map position={position} zoom={zoom} />}
    </div>
  );
}
