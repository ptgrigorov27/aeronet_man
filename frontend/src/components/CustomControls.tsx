import React, { useRef, useEffect } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";

const CustomControls: React.FC = () => {
  const map = useMap();

  const attributionControlRef = useRef<L.Control | null>(null);
  const githubControlRef = useRef<L.Control | null>(null);
  const reportControlRef = useRef<L.Control | null>(null);

  useEffect(() => {
    if (!map) {
      return;
    }

    // Add attribution control only once
    if (!attributionControlRef.current) {
      const attributionControl = L.control
        .attribution({ position: "bottomright" })
        .addAttribution(
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        )
        .setPrefix('<a href="https://leafletjs.com/">Leaflet</a>');
      attributionControl.addTo(map);
      attributionControlRef.current = attributionControl;
    }

   

    // Report control
    if (!reportControlRef.current) {
      const reportControl = L.control({ position: "bottomright" });
      reportControl.onAdd = () => {
        const div = L.DomUtil.create("div", "report-link");
        div.innerHTML = `
          <a href='mailto:terrell.credle@nasa.gov?cc=pawan.gupta@nasa.gov&subject=[BUG REPORT] MAN VISUALIZATION TOOL&body=If applicable, please attach screenshots and explain the issue you are experiencing.' style="display: flex; align-items: center; color: red; background: rgba(255, 255, 255, 0.7); padding: 5px; border-radius: 0px;">
            <img src="https://www.openmoji.org/data/color/svg/1F41E.svg" alt="Report Issue" style="width: auto; height: 20px; margin-right: 8px;">
            <strong>Report an issue</strong>
          </a>
        `;
        div.style.marginBottom = "5px";
        div.style.marginRight = "0px";
        return div;
      };
      reportControl.addTo(map);
      reportControlRef.current = reportControl;
    }
 // GitHub control
    if (!githubControlRef.current) {
      const githubControl = L.control({ position: "bottomright" });
      githubControl.onAdd = () => {
        const div = L.DomUtil.create("div", "github-link");
        div.innerHTML = `
          <a href="https://github.com/rell/aeronet_man" target="_blank" style="display: flex; align-items: center; background: rgba(255, 255, 255, 0.7); padding: 5px; border-radius: 0px;">
            <img src="https://www.openmoji.org/data/color/svg/1F6DF.svg" alt="GitHub" style="width: auto; height: 20px; margin-right: 8px;">
            <strong>Repository</strong>
          </a>
        `;
        div.style.marginBottom = "5px";
        div.style.marginRight = "0px";
        return div;
      };
      githubControl.addTo(map);
      githubControlRef.current = githubControl;
    }
    return () => {
      // to remove controls 
      // if (githubControlRef.current) map.removeControl(githubControlRef.current);
      // if (reportControlRef.current) map.removeControl(reportControlRef.current);
      // if (attributionControlRef.current) map.removeControl(attributionControlRef.current);
    };
  }, [map]);

  return null;
};

export default CustomControls;
