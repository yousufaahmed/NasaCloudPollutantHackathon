export default async function Home() {
  const title = "Frontend Developer"; // Set your desired title here
  const role = await fetchEngineerRole(title);

  return (
    <>
      <div>{`The main skill of a ${role?.title ?? title} is ${
        role?.mainskill ?? "unknown"
      }.`}</div>
    </>
  );
}

async function fetchEngineerRole(title: string) {
  const baseUrl = process.env.BASE_URL;

  try {
    const response = await fetch(
      `${baseUrl}/api/py/engineer-roles?title=${title}`
    );
    if (!response.ok) {
      throw new Error("Failed to fetch data");
    }
    const role = await response.json();
    return role;
  } catch (error) {
    console.error("Error fetching engineer role:", error);
    return null;
  }
}
