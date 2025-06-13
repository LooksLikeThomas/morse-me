import React from 'react';
import './App.css';
import Header from "./components/Header";
import Learn from "./components/Learn";
import MorseChat from "./components/Chat";

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <Header />
      </header>
      <div className="App-body flex justify-around items-center">
          <div className="flex align-middle w-[354px]">
              User Info / Scoreboard
          </div>
          <div className="chat-room flex align-middle">
            <MorseChat />
          </div>
          <div className="flex align-middle h-fit">
              <Learn />
          </div>
      </div>
    </div>
  );
}

export default App;