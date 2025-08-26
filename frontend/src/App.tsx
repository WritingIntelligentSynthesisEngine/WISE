import { useState, useEffect } from "react";
import reactLogo from "./assets/react.svg";
import viteLogo from "/vite.svg";
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
      <div>
        <a target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        <h2>后端请求测试:</h2>
        <p>{backendData}</p>
      </div>
    </>
  );
}

export default App;
