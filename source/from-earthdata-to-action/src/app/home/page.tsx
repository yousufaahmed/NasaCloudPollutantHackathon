export default async function Home() {
  return (
    <div>
      <h1 className="text-4xl font-bold mb-4 text-center">
        Welcome to Cleanview
      </h1>
      <div className="flex w-full px-[5%] font-mono">
        <div className="card bg-base-300 rounded-box grid h-40 grow place-items-center">
          Breathe Easy with Cleanview!!
        </div>
        <div className="divider divider-horizontal"></div>
        <div className="card bg-base-300 rounded-box grid h-40 grow place-items-center">
          Cleanview helps you stay one step ahead for a healthier day. Using
          TEMPO data, it smartly blends weather and local air info to give you
          the clearest picture possible. Cleanview's got you covered with tech
          thats fresh, and clean.
        </div>
      </div>
    </div>
  );
}
