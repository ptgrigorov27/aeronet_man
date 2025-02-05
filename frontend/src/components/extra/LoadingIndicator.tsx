import React from "react";
import "./LoadingIndicator.css";

const LoadingIndicator: React.FC = () => {
  return (
    <div className="loading-overlay">
      <div className="loading-spinner"></div>
      <div className="loading-text">
        Please do not close the page...
        <br />
        Your requested MAN dataset is processing - download will begin shortly.
      </div>
    </div>
  );
};

export default LoadingIndicator;
