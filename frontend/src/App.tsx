import React, { useState, useEffect } from "react";
import MapComponent from "./components/MapComponent";
import SidePanel from "./components/SidePanel";
import { MapProvider } from "./components/MapContext";
import { SiteProvider } from "./components/SiteContext";
import { getCookie } from "./components/utils/csrf";
import API_BASE_URL from "./config";
import axios from "axios";
import "./App.css";

const App: React.FC = () => {
  const [csrfToken, setCsrfToken] = useState<string | null>(null);
  const center: [number, number] = [0, 0];
  const zoom = 2;

  useEffect(() => {
    const fetchCsrfToken = async () => {
      try {
        await axios.get(`${API_BASE_URL}/maritimeapp/set-csrf/`, {
          withCredentials: true,
        });
        const token = getCookie("test");
        setCsrfToken(token);
      } catch (error) {
        console.error("Error fetching CSRF token:", error);
      }
    };

    fetchCsrfToken();
  }, []);

  return (
    <SiteProvider>
      <MapProvider>
        <div className="App" style={{ display: "flex" }}>
          <MapComponent center={center} zoom={zoom} type={"aod_500nm"} />
          <SidePanel />
        </div>
      </MapProvider>
    </SiteProvider>
  );
};

export default App;
