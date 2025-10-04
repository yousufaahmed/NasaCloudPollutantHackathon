"use client";

import Link from "next/link";

export default function Navbar() {
  const navbarItems: string[] = [];

  navbarItems.push("Home", "Dashboard");
  return (
    <nav className="w-full max-w-screen px-4 py-4 mx-auto flex top-0 left-0 z-50 menu-toggle justify-center">
      <ul className="menu-links">
        {navbarItems.map((item) => (
          <Link
            key={item}
            href={`/${item.toLowerCase()}`}
            className="text-3xl mx-2 text-black hover:text-gray-300 transition-colors duration-200 font-mono"
          >
            {item}
          </Link>
        ))}
      </ul>
    </nav>
  );
}
