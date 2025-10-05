import Image from "next/image";

export default async function Home() {
  return (
    <div className="flex flex-col items-center justify-center max-w-3xl mx-auto py-8 px-4 font-mono">
      <div className="flex flex-col gap-6 text-black dark:text-white transition-colors duration-700">
        <div className="card bg-base-300 rounded-box p-4">
          Cleanview helps you stay one step ahead for a healthier day. Using
          TEMPO data, it smartly blends weather and local air info to give you
          the clearest picture possible. Cleanview has got you covered with tech
          thats fresh, and clean.
        </div>
        Check out the dashboard to see the air quality in certain areas. You
        will also see our weather widget that shows the current weather and
        humidity in your area!
      </div>
      <div className="card bg-base-300 rounded-box h-[5%] py-4 mt-4 flex flex-row">
        <div className="card bg-base-300 rounded-box p-4 flex flex-row items-center">
          <Image
            src={"/images/team_photo.png"}
            width={"200"}
            height={"100"}
            alt="Group photo of the team"
            className="rounded-lg flex-shrink-0"
          />
          <p className="px-4">
            This is our team, consisting of a bunch of students from the
            University of the Exeter. We worked really hard on this throughout
            the night and we hope you appreciate our time and effort in this
            submission!
          </p>
        </div>
      </div>
    </div>
  );
}
