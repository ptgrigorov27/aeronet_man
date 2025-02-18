import React from "react";
import "./LoadingIndicator.css";

const LoadingIndicator: React.FC = () => {
  return (
    <div className="loading-overlay">
    
      <div className="container">
      <div className="loading-spinner"></div>
      <div className="loading-text">
        Please do not close the page...
        <br />
        Your custom MAN dataset is processing and download will begin shortly.
      
        <br />

        <hr/>
         <sup> INFO: A full cruise selection download with all available options selected may take anywhere from 1 minute to 5 minutes depending on server load.</sup>
       

        <br />
         <span className="text-danger"><sup> If you notice your download is not being properly created or is incorrect. Please use the report button located in the bottom right corner to notify us.</sup> </span>
      </div>
        </div>
    </div>
  );
};

export default LoadingIndicator;
