import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import ContractUpload from './components/ContractUpload';
import ContractList from './components/ContractList';
import ContractDetail from './components/ContractDetail';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App min-h-screen bg-gray-50">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<ContractUpload />} />
            <Route path="/contracts" element={<ContractList />} />
            <Route path="/contracts/:contractId" element={<ContractDetail />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
