import { useState, useEffect } from "react";
import "./App.css";

function App() {
  const [backendData, setBackendData] = useState("正在请求后端...");

  useEffect(() => {
    fetch("/api/core/hello")
      .then((response) => {
        if (!response.ok) {
          throw new Error(`网络响应不正常 (${response.status})`);
        }
        return response.text();
      })
      .then((text) => {
        setBackendData(text);
      })
      .catch((error) => {
        setBackendData(`无法从后端加载数据: ${error.message}`);
      });
  }, []);

  return (
    <>
      <p className="text-3xl font-bold">后端请求测试:</p>
      <p className="text-3xl underline">{backendData}</p>
    </>
  );
}

export default App;
