"use client";
import { useState, useEffect } from "react";

export default function DarkModeToggle() {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const darkPref =
      localStorage.getItem("color-theme") === "dark" ||
      (!("color-theme" in localStorage) &&
        window.matchMedia("(prefers-color-scheme: dark)").matches);

    setIsDark(darkPref);
    document.documentElement.setAttribute(
      "data-theme",
      darkPref ? "dark" : "light"
    );
  }, []);

  const handleToggle = () => {
    const newDark = !isDark;
    setIsDark(newDark);
    document.documentElement.setAttribute(
      "data-theme",
      newDark ? "dark" : "light"
    );
    localStorage.setItem("color-theme", newDark ? "dark" : "light");
  };

  return (
    <button
      onClick={handleToggle}
      aria-label="Toggle dark mode"
      className="p-2 rounded-full bg-white/20 hover:bg-white/40 transition"
    >
      <svg
        width="24"
        height="24"
        fill="none"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
        className={`transition-transform duration-500 ${
          isDark ? "rotate-180 text-yellow-400" : "rotate-0 text-slate-700"
        }`}
      >
        <path
          d="M21 12.79A9 9 0 0 1 12.79 3a1 1 0 0 0-1.13 1.36A7 7 0 1 0 19.64 13.92a1 1 0 0 0 1.36-1.13Z"
          fill="currentColor"
        />
      </svg>
    </button>
  );
}
