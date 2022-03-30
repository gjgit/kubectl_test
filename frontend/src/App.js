import React, { useState } from "react";
import "./App.css";
import axios from "axios";
import "bootstrap/dist/css/bootstrap.min.css";

function App() {
  const [number, setNumber] = useState("");

  function sample(result) {
    document.getElementById("text_a").innerHTML = result;
  }

  // Post a todo
  const squareHandler = () => {
    axios.post("/square", { number: number }).then((res) => {
      sample(res.data);
    });
  };

  return (
    <>
      <input
        onChange={(event) => setNumber(event.target.value)}
        placeholder="Number"
      />
      <button onClick={squareHandler}>Square</button>
      <h1 id="text_a"></h1>
    </>
  );
}

export default App;
