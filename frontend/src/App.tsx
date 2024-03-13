import React from "react";
import { useState, useEffect } from "react";

interface IJSONUserResponse {
  users: string[];
}

function App() {
  const [data, setData] = useState<string[]>();
  useEffect(() => {
    const fetchData = async () => {
      const res = await fetch("/users");
      const data = (await res.json()) as IJSONUserResponse;
      setData(data.users);
      console.log(data.users);
    };

    fetchData();
  }, []);

  return (
    <div>
      {data?.map((user) => (
        <h2>{user}</h2>
      ))}
    </div>
  );
}

export default App;
