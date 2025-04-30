import React from "react";
import "./LoadingIndicator.css";

const LoadingIndicator: React.FC = () => {
  return (
    <div className="loading-overlay">
      <div className="container">
        <div className="loading-spinner" style={{ margin: "0 auto;" }}></div>
        <div className="loading-text">
          <br />
          <h4>Please do not close the page.</h4>
          Your request is processing and the download will begin shortly.
          <br />
          <hr />
          <span className="text-danger">
            <sup>
              {" "}
              If you notice your download is not being properly created or is
              incorrect. Please submit a report with the button located in the
              bottom right corner.
            </sup>{" "}
          </span>
        </div>
      </div>
    </div>
  );
};

export default LoadingIndicator;

