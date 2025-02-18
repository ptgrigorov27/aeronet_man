import React, { useState, useCallback, useEffect, ChangeEvent } from "react";
import { Card, Button, Modal, Form } from "react-bootstrap";
import { useMapContext } from "./MapContext";
import SiteManager from "./forms/SiteManager";
import SiteSelectionForm from "./forms/SiteSelection";
import { useSiteContext } from "./SiteContext";
import styles from "./SidePanel.module.css";
import L from "leaflet";
import "leaflet-draw";
import axios from "axios";
import LoadingIndicator from "./extra/LoadingIndicator";
import API_BASE_URL from "../config";
import ColorLegend from "./colorScale";
import { getCookie } from "./utils/csrf";

export interface SiteSelect {
  name: string;
  span_date: [string, string];
}

const SidePanel: React.FC = () => {
  const { map } = useMapContext();
  const { setBounds, sites } = useSiteContext();
  const [zoomLevel, setZoomLevel] = useState(map?.getZoom() || 2);
  const [showModal, setShowModal] = useState(false);
  const [isSet, setIsSet] = useState(false);
  const [markerSize, setMarkerSize] = useState<number>(4);
  const [showDownloadModal, setShowDownloadModal] = useState(false);
  const [showDataModal, setShowDataModal] = useState(false);
  const [selectedSites, setSelectedSites] = useState<Set<string>>(new Set());
  const [startDate, setStartDate] = useState<string>("");
  const [tempSelectedSites, setTempSelectedSites] = useState<Set<string>>(
    new Set(),
  );
  const [refreshMarkers, setRefreshMarkers] = useState<boolean>(false);
  const [refreshMarkerSize, setRefreshMarkerSize] = useState<boolean>(false);
  const [typeChanged, setTypeChange] = useState<boolean>(false);
  const [endDate, setEndDate] = useState<string>("");
  const [minLat, setMinLat] = useState<number>();
  const [minLng, setMinLng] = useState<number>();
  const [maxLat, setMaxLat] = useState<number>();
  const [maxLng, setMaxLng] = useState<number>();
  const [rectangle, setRectangle] = useState<L.Rectangle | null>(null);
  const [drawing, setDrawing] = useState(false);
  const [rectangleDrawn, setRectangleDrawn] = useState(false);
  const [showLoading, setShowLoading] = useState(false);
  const [dataValue, setDataValue] = useState<string>("aod_500nm");
  const [displayOpts, setDisplayOpts] = useState<Set<string>>(new Set());
  const [traceActive, setTraceActive] = useState(false);
  const [filterValue, setFilterValue] = useState<string>("");
  const [filterSym, setFilterSym] = useState<string>("");
  const [fetchedSites, setFetchedSites] = useState<Set<string>>(new Set());
  const [showNotification, setShowNotification] = useState<boolean>(false);
  const [responseSucess, setResponseSuccess] = useState<boolean>(false);
  interface DisplayInfoResponse {
    opts: string[];
  }

  // On site load
  useEffect(() => {
    const fetchDisplayInfo = async () => {
      try {
        const response = await axios.get<DisplayInfoResponse>(
          `${API_BASE_URL}/maritimeapp/display_info`,
          {
            responseType: "json",
          },
        );
        setDisplayOpts(new Set(response.data.opts));
      } catch (error) {
        console.error("Error fetching display options:", error);
      }
    };
    setTimeout(() => {
      fetchDisplayInfo();
      setZoomLevel(2);
      setMarkerSize((zoomLevel + 2) * (Math.E - 1));
    }, 500);
  }, []);

  //NOTE: This updates the map on these values change
  useEffect(() => {
    setTimeout(() => {
      updateMap();
    }, 500);
  }, [selectedSites, dataValue, maxLng]);

  useEffect(() => {
    setMarkerSize((zoomLevel + 2) * (Math.E - 1));
  }, [zoomLevel]);

  useEffect(() => {
    if (map) {
      const onZoom = () => {
        setZoomLevel(map.getZoom());
      };
      map.on("zoomend", onZoom);
      return () => {
        map.off("zoomend", onZoom);
      };
    }
  }, [map, zoomLevel]);

  useEffect(() => {
    handleBoundaryChange();
  }, [minLat, minLng, maxLat, maxLng]);

  useEffect(() => {
    if (showNotification) {
      const timer = setTimeout(() => {
        setShowNotification(false);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [showNotification]);

  {
    /* handle download */
  }
  // State for download options
  const [selectedRetrieval, setSelectedRetrieval] = useState<Set<string>>(
    new Set(),
  );
  const [selectedFrequency, setSelectedFrequency] = useState<Set<string>>(
    new Set(),
  );
  const [selectedQuality, setSelectedQuality] = useState<Set<string>>(
    new Set(),
  );
  const handleToggleDownloadModal = () => {
    setShowDownloadModal((prev) => !prev);
  };
  const handleToggleDataModal = () => {
    setShowDataModal((prev) => !prev);
  };

  const handleToggleModal = () => {
    setShowModal(true);
  };

  const updateType = () => {
    setTypeChange(true);
    setTimeout(() => {
      setTypeChange(false);
    }, 100);
  };

  const updateMarkerSize = () => {
    setRefreshMarkerSize(true);
    setTimeout(() => {
      setRefreshMarkerSize(false);
    }, 100);
  };
  const updateMap = () => {
    setRefreshMarkers(true);
    setTimeout(() => {
      setRefreshMarkers(false);
    }, 100);
  };

  const handleOptionToggle = (
    option: string,
    setSelectedOptions: React.Dispatch<React.SetStateAction<Set<string>>>,
  ) => {
    setSelectedOptions((prev) => {
      const newSelection = new Set(prev);
      if (newSelection.has(option)) {
        newSelection.delete(option);
      } else {
        newSelection.add(option);
      }
      return newSelection;
    });
  };

  const handleDownload = async () => {
    const params = {
      sites: Array.from(selectedSites),
      min_lat: minLat,
      min_lng: minLng,
      max_lat: maxLat,
      max_lng: maxLng,
      start_date: startDate,
      end_date: endDate,
      retrievals: Array.from(selectedRetrieval),
      frequency: Array.from(selectedFrequency),
      quality: Array.from(selectedQuality),
    };

    console.log("DOWNLOAD -> selectedSites", selectedSites);

    setShowLoading(true); // Show the download processing indicator
    try {
      const filteredParams = Object.fromEntries(
        Object.entries(params).filter(([_, v]) => v != null),
      );
      const csrfToken = getCookie("X-CSRFToken");
      const response = await fetch(`${API_BASE_URL}/maritimeapp/download/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken || "",
        },
        body: JSON.stringify(filteredParams),
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const disposition = response.headers.get("content-disposition");
      const filenameMatch = disposition
        ? disposition.match(/filename="?(.+)"?/)
        : null;
      const filename = filenameMatch ? filenameMatch[1] : "man_dataset.tar.gz";
      if (filename.charAt(str.length - 1) === "_") {
         filename = str.slice(0, -1);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);
    } catch (error) {
      console.error("Error during download:", error);
    } finally {
    
      setShowNotification(true);
      setTimeout(() => {
        setShowNotification(false);
      }, 5000);
      setShowLoading(false); // Show the download processing indicator
    }
    setShowDownloadModal(false);
  };
  {
    /********************/
  }
  const handleDone = () => {
    console.log("ON SAVE DATE: ", startDate, endDate);
    localStorage.setItem("startDate", startDate);
    localStorage.setItem("endDate", endDate);

    setSelectedSites(tempSelectedSites);
    setShowModal(false);
    setIsSet(true);
    setTimeout(() => {
      setIsSet(false);
    }, 100);
  };

  const handleDateChange = useCallback(
    (newStartDate: string, newEndDate: string) => {
      if (
        newStartDate &&
        newEndDate &&
        (startDate != newStartDate || endDate != newEndDate)
      ) {
        console.log(`Date changed\n${newStartDate} \n${newEndDate}`);
        setStartDate(newStartDate);
        setEndDate(newEndDate);
      }
    },
    [startDate, endDate],
  );

  const handleZoomChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const zoom = parseInt(event.target.value, 10);
    if (map) {
      map.setZoom(zoom);
      setZoomLevel(zoom);
    }
  };

  const handleDataTypeChange = (
    event: React.ChangeEvent<HTMLSelectElement>,
  ) => {
    setDataValue(event.target.value);
  };

  const handleFilterSym = (event: ChangeEvent<HTMLSelectElement>) => {
    setFilterSym(event.target.value);
  };

  const handleSelectionChangeTemp = (
    newSelectedSites: Set<string>,
    type: string,
  ) => {
    //console.log("ONCHANGE", newSelectedSites);
    setTempSelectedSites(newSelectedSites);
  };

  const drawAction = () => {
    if (map && !drawing) {
      setDrawing(true);

      const drawHandler = new L.Draw.Rectangle(map, {
        shapeOptions: {
          color: "#ff0000",
          weight: 2,
          fill: false,
          opacity: 1,
        },
      });

      drawHandler.enable();

      type DrawCreatedEvent = L.LeafletEvent & {
        layer: L.Layer & {
          getBounds: () => L.LatLngBounds;
        };
      };

      map.once("draw:created", (event: DrawCreatedEvent) => {
        const { layer } = event;
        const bounds = layer.getBounds();

        if (rectangle) {
          map.removeLayer(rectangle);
        }

        // Getting bnoundries
        const sw = bounds.getSouthWest();
        const ne = bounds.getNorthEast();

        // Out of bounds correction
        const minLat = Math.max(-90, Math.min(90, sw.lat));
        const minLng = Math.max(-180, Math.min(180, sw.lng));
        const maxLat = Math.max(-90, Math.min(90, ne.lat));
        const maxLng = Math.max(-180, Math.min(180, ne.lng));

        const correctedBounds = L.latLngBounds(
          L.latLng(minLat, minLng),
          L.latLng(maxLat, maxLng),
        );

        const newBounds = L.rectangle(correctedBounds, {
          color: "#ff0000", // Red outline
          weight: 2,
          fill: false, // No fill
        }).addTo(map);

        setRectangle(newBounds);

        setMinLat(minLat);
        setMinLng(minLng);
        setMaxLat(maxLat);
        setMaxLng(maxLng);
        setBounds(bounds);

        setRectangleDrawn(true);

        drawHandler.disable();
        setDrawing(false);
      });
    }
  };

  const handleFilterValue = (event: ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    // Regex pattern to match float values
    const floatPattern = /^-?\d*(\.\d*)?$/;
    if (floatPattern.test(value) || value === "") {
      setFilterValue(value);
    }
  };
  const handleBoundaryChange = () => {
    if (rectangle && map) {
      const bounds = new L.LatLngBounds(
        new L.LatLng(minLat || 0, minLng || 0),
        new L.LatLng(maxLat || 0, maxLng || 0),
      );
      rectangle.setBounds(bounds);
      //map.fitBounds(bounds);
      updateSet();
    }
  };

  const handleClearBounds = () => {
    // Remove the rectangle from the map and reset bounds
    if (rectangle) {
      map?.removeLayer(rectangle);
      setRectangle(null);
    }
    setBounds(null);
    setMinLat(undefined);
    setMinLng(undefined);
    setMaxLat(undefined);
    setMaxLng(undefined);

    setRectangleDrawn(false);
  };

  const siteOptions: SiteSelect[] = sites.map((site) => ({
    name: site.name,
    span_date: site.span_date
      ? [site.span_date[0], site.span_date[1]]
      : ["", ""],
  }));

  const updateSet = async () => {
    const fetchSites = async () => {
      try {
        const params = new URLSearchParams();
        if (startDate) params.append("start_date", startDate);
        if (endDate) params.append("end_date", endDate);
        if (
          minLat !== undefined &&
          minLng !== undefined &&
          maxLat !== undefined &&
          maxLng !== undefined
        ) {
          params.append("min_lat", minLat.toString());
          params.append("min_lng", minLng.toString());
          params.append("max_lat", maxLat.toString());
          params.append("max_lng", maxLng.toString());
        }

        const response = await fetch(
          `${API_BASE_URL}/maritimeapp/measurements/sites/?${params.toString()}`,
        );
        const returned: SiteSelect[] = await response.json();

        setFetchedSites(new Set(returned.map((site) => site.name)));
      } catch (error) {
        console.error("Error fetching sites:", error);
      }
    };

    await fetchSites();
  };

  useEffect(() => {
    if (fetchedSites.size > 0) {
      const newSelection = new Set<string>(
        Array.from(selectedSites).filter((siteName) =>
          fetchedSites.has(siteName),
        ),
      );
      setSelectedSites(newSelection);
    }
  }, [fetchedSites]);

  return (
    <>
      <ColorLegend type={dataValue} activateTrace={traceActive} />
      {traceActive && (
        <div
          style={{
            position: "fixed",
            bottom: "50px",
            left: "50%",
            transform: "translateX(-50%)",
            backgroundColor: "#FFFFFFAF",
            padding: "0.5rem 1rem",
            borderRadius: "5px",
            color: "#000",
            zIndex: 9999,
            width: "auto",
            textAlign: "center",
            pointerEvents: "none",
            border: "2px solid rgba(255, 255, 255, 0.5)",
          }}
        >
          Double click a visible marker <br /> to exit isolated path mode.
        </div>
      )}
      {showNotification && (
        <div
          style={{
            position: "fixed",
            bottom: "50px",
            left: "50%",
            transform: "translateX(-50%)",
            backgroundColor: "#0d6efdFF",
            padding: "0.5rem 1rem",
            borderRadius: "5px",
            color: "white",
            zIndex: 9999,
            width: "auto",
            textAlign: "center",
            pointerEvents: "none",
            border: "2px solid rgba(255, 255, 255, 0.5)",
            transition: "opacity 0.5s ease-in-out",
            opacity: showNotification ? 1 : 0,
          }}
        >
          ⛵ Download started successfully!
        </div>
      )}
      <Card className={styles.sidePanel}>
        <Card.Body>
          <Card.Title>Map Controls</Card.Title>
          <div className={styles.buttonGroup}>
            <div className={styles.sliderContainer}>
              <input
                type="range"
                min={1}
                max={19}
                step={1}
                value={zoomLevel}
                onChange={handleZoomChange}
                className={styles.slider}
              />
              <div className={styles.sliderLabel}>Zoom Level: {zoomLevel}</div>
            </div>
            <Button
              variant="warning"
              onClick={() => map && map.setView([0, 0], 2)}
            >
              Reset View
            </Button>
            <div className={styles.buttonContainer}>
              <SiteManager
                startDate={startDate}
                markerSize={markerSize}
                endDate={endDate}
                minLat={minLat}
                minLng={minLng}
                maxLat={maxLat}
                maxLng={maxLng}
                refreshMarkers={refreshMarkers}
                refreshMarkerSize={refreshMarkerSize}
                type={dataValue}
                traceActive={traceActive}
                zoom={zoomLevel}
                sitesSelected={isSet}
                typeChanged={typeChanged}
                selectedSites={selectedSites}
                setTraceActive={setTraceActive}
              >
                <Button
                  style={{ marginRight: "5px" }}
                  variant="success"
                  className={styles.customButton}
                  onClick={drawAction}
                >
                  Draw Bounds
                </Button>
              </SiteManager>

              <Button
                variant="danger"
                className={styles.customButton}
                onClick={handleClearBounds}
              >
                Clear Bounds
              </Button>
            </div>
          </div>
          {rectangleDrawn && (
            <div className={styles.boundaryInputs}>
              <Form>
                <div className={styles.inputRow}>
                  <Form.Group className={styles.inputGroup}>
                    <Form.Label>Min Lat</Form.Label>
                    <Form.Control
                      type="number"
                      value={minLat || ""}
                      onChange={(e) => setMinLat(parseFloat(e.target.value))}
                      onBlur={handleBoundaryChange}
                    />
                  </Form.Group>
                  <Form.Group className={styles.inputGroup}>
                    <Form.Label>Min Lng</Form.Label>
                    <Form.Control
                      type="number"
                      value={minLng || ""}
                      onChange={(e) => setMinLng(parseFloat(e.target.value))}
                      onBlur={handleBoundaryChange}
                    />
                  </Form.Group>
                </div>
                <div className={styles.inputRow}>
                  <Form.Group className={styles.inputGroup}>
                    <Form.Label>Max Lat</Form.Label>
                    <Form.Control
                      type="number"
                      value={maxLat || ""}
                      onChange={(e) => setMaxLat(parseFloat(e.target.value))}
                      onBlur={handleBoundaryChange}
                    />
                  </Form.Group>
                  <Form.Group className={styles.inputGroup}>
                    <Form.Label>Max Lng</Form.Label>
                    <Form.Control
                      type="number"
                      value={maxLng || ""}
                      onChange={(e) => setMaxLng(parseFloat(e.target.value))}
                      onBlur={handleBoundaryChange}
                    />
                  </Form.Group>
                </div>
              </Form>
            </div>
          )}

          <hr className={styles.separator} />
          <Card.Title>Configuration</Card.Title>
          <div className={styles.buttonGroup}>
            <Button variant="secondary" onClick={handleToggleModal}>
              Cruise Selection
            </Button>
            <Button variant="secondary" onClick={handleToggleDataModal}>
              Display Data
            </Button>
          </div>
          <hr className={styles.separator} />
          {/* remove redundant title for download */}
          {/*<Card.Title>Download</Card.Title>*/}
          <div>
            {/*<Button
              variant="primary"
              onClick={updateMap} 
              className="w-100"
            >
              Update Preview
            </Button> */}
            <Button
              variant="primary"
              onClick={handleToggleDownloadModal}
              className="w-100"
            >
              Download
            </Button>
          </div>
        </Card.Body>
      </Card>
      {/* Download Modal */}
      <Modal
        show={showDownloadModal}
        onHide={handleToggleDownloadModal}
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>Download Data</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div>
            {/* Download Animation */}
            {showLoading && <LoadingIndicator />}{" "}
          </div>
          <h5>Retrieval Options</h5>
          <div className={styles.downloadOptions}>
            {["AOD", "SDA"].map((option) => (
              <Button
                key={option}
                variant={
                  selectedRetrieval.has(option) ? "primary" : "outline-primary"
                }
                onClick={() => handleOptionToggle(option, setSelectedRetrieval)}
                className={styles.optionButton}
              >
                {option}
              </Button>
            ))}
          </div>
          <h5>Reading Frequency</h5>
          <div className={styles.downloadOptions}>
            {["Point", "Series", "Daily"].map((option) => (
              <Button
                key={option}
                variant={
                  selectedFrequency.has(option) ? "primary" : "outline-primary"
                }
                onClick={() => handleOptionToggle(option, setSelectedFrequency)}
                className={styles.optionButton}
              >
                {option}
              </Button>
            ))}
          </div>
          <h5>Reading Quality</h5>
          <div className={styles.downloadOptions}>
            {["Level 1.0", "Level 1.5", "Level 2.0"].map((option) => (
              <Button
                key={option}
                variant={
                  selectedQuality.has(option) ? "primary" : "outline-primary"
                }
                onClick={() => handleOptionToggle(option, setSelectedQuality)}
                className={styles.optionButton}
              >
                {option}
              </Button>
            ))}
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleToggleDownloadModal}>
            Close
          </Button>
          <Button variant="primary" onClick={handleDownload}>
            Download
          </Button>
        </Modal.Footer>
      </Modal>
      {/* Cruise Selection Modal*/}
      <Modal show={showModal} onHide={() => setShowModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Cruise Selection</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <SiteManager
            startDate={startDate}
            endDate={endDate}
            minLat={minLat}
            minLng={minLng}
            maxLat={maxLat}
            maxLng={maxLng}
            markerSize={markerSize}
            refreshMarkerSize={refreshMarkerSize}
            refreshMarkers={refreshMarkers}
            zoom={zoomLevel}
            type={dataValue}
            traceActive={traceActive}
            sitesSelected={isSet}
            typeChanged={typeChanged}
            selectedSites={selectedSites}
            setTraceActive={setTraceActive}
          >
            {showModal ? (
              <SiteSelectionForm
                isModalShown={showModal}
                sites={siteOptions}
                selectedSites={selectedSites}
                bounds={[minLat || 0, minLng || 0, maxLat || 0, maxLng || 0]}
                onSelectionChange={handleSelectionChangeTemp}
                onDateChange={handleDateChange}
              />
            ) : (
              <></>
            )}
          </SiteManager>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleDone}>
            Done
          </Button>
        </Modal.Footer>
      </Modal>
      <Modal show={showDataModal} onHide={handleToggleDataModal} centered>
        <Modal.Header closeButton>
          <Modal.Title>Data Display</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <Card.Header style={{ fontWeight: "bold" }}>DATA TYPE</Card.Header>
            <Form.Select
              style={{ width: "75%" }}
              value={dataValue}
              onChange={handleDataTypeChange}
              aria-label="Select display option"
            >
              {!displayOpts.has("aod_500nm") && (
                <option value="aod_500nm">aod_500nm</option>
              )}

              {Array.from(displayOpts).map((opt, index) => (
                <option key={index} value={opt}>
                  {opt}
                </option>
              ))}
            </Form.Select>
          </div>
          <br />
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "right",
            }}
          >
            {/* 
          <Card.Header style={{ fontWeight: "bold" }}>
              VALUE FILTER
            </Card.Header>
            <Form.Select
              style={{ width: "20%" }}
              value={filterSym}
              onChange={handleFilterSym}
              aria-label="Select display option"
            >
              {!displayOpts.has(" ") && (
                <>
                  <option value="gt">&gt;</option>
                  <option value="lt">&lt;</option>
                  <option value="eq">=</option>
                  <option value="gte">&gt;=</option>
                  <option value="lte">&lt;=</option>
                </>
              )}
            </Form.Select>
            <Form.Control
              type="float"
              value={filterValue}
              onChange={handleFilterValue}
              placeholder="Enter float value"
              aria-label="Float value input"
              pattern="^-?\d*(\.\d*)?$"
              style={{ marginLeft: "10px", width: "50%" }}
            />
            */}
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleToggleDataModal}>
            Done
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
};

export default SidePanel;
