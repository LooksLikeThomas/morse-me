import React from 'react';
import './App.css';
import Header from "./components/Header";
import Learn from "./components/Learn";

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <Header />
      </header>
      <div className="App-body flex justify-between items-center">
          <div className="flex align-middle">
              User Info / Scoreboard
          </div>
          <div className="chat-room flex align-middle">
            chat
          </div>
          <div className="flex align-middle h-fit">
              <Learn />
          </div>
      </div>
    </div>
  );
}

export default App;