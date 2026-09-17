import React, { useState } from "react";
import LoginForm from "./components/LoginForm.jsx";
import Dashboard from "./components/Dashboard.jsx";

export default function App() {
  const [session, setSession] = useState(null);

  return (
    <div className="app-shell">
      <h1>Secure Question-Paper Management System</h1>
      {!session ? (
        <LoginForm onLogin={setSession} />
      ) : (
        <Dashboard session={session} onLogout={() => setSession(null)} />
      )}
    </div>
  );
}
