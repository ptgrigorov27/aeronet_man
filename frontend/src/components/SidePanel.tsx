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

export interface SiteSelect {
    name: string;
    span_date: [string, string];
}

const SidePanel: React.FC = () => {
    const { map } = useMapContext();
    const { setBounds, sites } = useSiteContext();
    const [zoomLevel, setZoomLevel] = useState(map?.getZoom() || 2);
    const [showModal, setShowModal] = useState(false);
    const [markerSize, setMarkerSize] = useState<number>(4);
    const [showDownloadModal, setShowDownloadModal] = useState(false);
    const [showDataModal, setShowDataModal] = useState(false);
    const [selectedSites, setSelectedSites] = useState<Set<string>>(new Set());
    const [startDate, setStartDate] = useState<string>("");
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
    const [filterValue, setFilterValue] = useState<string>('');
    const [filterSym, setFilterSym] = useState<string>('')
    interface DisplayInfoResponse {
        opts: string[]; 
    }


    //set initial marker size
    useEffect(()=>{
        setMarkerSize(4);
    },[]);


    useEffect(() => {
        if (map) {
            const onZoom = () => {
                setZoomLevel(map.getZoom());
            };

            // Add the event listener for 'zoomend'
            map.on("zoomend", onZoom);
            return () => {
                map.off("zoomend", onZoom);
            };
        }
    }, [map, zoomLevel]);

    useEffect(() => {
        const fetchDisplayInfo = async () => {
            try {
                const response = await axios.get<DisplayInfoResponse>(`${API_BASE_URL}/maritimeapp/display_info`, {
                    responseType: 'json',
                });
                // Convert the array of options into a Set
                setDisplayOpts(new Set(response.data.opts));
            } catch (error) {
                console.error('Error fetching display options:', error);
            }
        };

        fetchDisplayInfo();
    }, []);


    useEffect(()=>{
        handleBoundaryChange();
    }, [minLat, minLng, maxLat, maxLng]);
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
        setShowModal((prev) => !prev);
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

        console.log("Download Params:", params);

        setShowLoading(true); // Show the download processing indicator

        try {
            const response = await axios.get(`${API_BASE_URL}/maritimeapp/download`, {
                params,
                responseType: "blob",
            });

            // TODO: Fix the filename extraction
            const disposition = response.headers["content-disposition"];
            const filenameMatch = disposition
                ? disposition.match(/filename="(.+)"/)
                : null;
                const filename = filenameMatch ? filenameMatch[1] : "man_dataset.tar.gz";
                const url = window.URL.createObjectURL(new Blob([response.data]));

                // Create a link element
                const link = document.createElement("a");
                link.href = url;
                link.setAttribute("download", filename);
                document.body.appendChild(link);
                link.click();
                // Post click remove element
                window.URL.revokeObjectURL(url);
                document.body.removeChild(link);
        } catch (error) {
            console.error("Error during download:", error);
        } finally {
            setShowLoading(false); // Removing the download indicator
        }
        setShowDownloadModal(false); // Close the download modal
    };
    {
        /********************/
    }
    const handleDateChange = useCallback((startDate: string, endDate: string) => {
        console.log("Date Range Updated:", startDate, endDate);
        setStartDate(startDate);
        setEndDate(endDate);
    }, []);

    const handleZoomChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const zoom = parseInt(event.target.value, 10);
        if (map) {
            map.setZoom(zoom);
            setZoomLevel(zoom);
        }
    };

    const handleDataTypeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        setDataValue(event.target.value); // Access the value of the selected option
    };

    const handleFilterSym = (event: ChangeEvent<HTMLSelectElement>) => {
        setFilterSym(event.target.value); // Access the value of the selected option
    };
    const handleSelectionChange = (
        newSelectedSites: Set<string>,
        type: string,
    ) => {
        setSelectedSites(newSelectedSites);
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
        if (floatPattern.test(value) || value === '') {
            setFilterValue(value);
        }

    }
    const handleBoundaryChange = () => {
        if (rectangle && map) {
            const bounds = new L.LatLngBounds(
                new L.LatLng(minLat || 0, minLng || 0),
                new L.LatLng(maxLat || 0, maxLng || 0),
            );
            rectangle.setBounds(bounds);
            //map.fitBounds(bounds);
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

    //useEffect(() => {
    //  console.log("Selected Sites Updated:", selectedSites);
    //}, [selectedSites]);

    //TODO: Refresh map redering and selected site list upon chnging of these values 
    //useEffect(() => {
    //}, [startDate, endDate, minLat]);

    return (
        <>
        <ColorLegend type={dataValue} activateTrace={traceActive}/>
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
        endDate={endDate}
        minLat={minLat}
        minLng={minLng}
        maxLat={maxLat}
        maxLng={maxLng}
        type={dataValue} 
        traceActive={traceActive}
        selectedSites={selectedSites}
        setTraceActive={setTraceActive}
        zoom={zoomLevel}
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
        <div >
        <Button
        variant="primary"
        onClick={handleToggleDownloadModal}
        className="w-100"
        >Download</Button>
        
        {/*
        <hr className={styles.separator} />
        <Button
        variant="danger"
        onClick={() => window.location.href = 'mailto:terrell.credle@nasa.gov?cc=pawan.gupta@nasa.gov&subject=' + encodeURIComponent('[BUG REPORT] MAN VISUALIZATION TOOL') + '&body=' + encodeURIComponent('If applicable, please attach screenshots and explain the issue you are experiencing.')}
        className="w-100 btn-sm"
        >
        Report an issue 
        </Button>
        */}
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

        {/* Cruise Selection Modal */}
        <Modal show={showModal} onHide={handleToggleModal} centered>
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
        type={dataValue} // TODO: Change this to be dynamically assigned by Configuration Modal
        traceActive={traceActive}
        selectedSites={selectedSites}
        setTraceActive={setTraceActive}
        >
        <SiteSelectionForm
        sites={siteOptions}
        selectedSites={selectedSites}
        bounds={[minLat || 0, minLng || 0, maxLat || 0, maxLng || 0]}
        onSelectionChange={handleSelectionChange}
        onDateChange={handleDateChange}
        />
        </SiteManager>
        </Modal.Body>
        <Modal.Footer>
        <Button variant="secondary" onClick={handleToggleModal}>
        Done
        </Button>
        </Modal.Footer>
        </Modal>

        <Modal show={showDataModal} onHide={handleToggleDataModal} centered>
        <Modal.Header closeButton>
        <Modal.Title>Data Display</Modal.Title>
        </Modal.Header>
        <Modal.Body>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Card.Header style={{ fontWeight: 'bold' }}>DATA TYPE</Card.Header>
        <Form.Select
        style={{ width: "75%"}}
        value={dataValue}
        onChange={handleDataTypeChange} 
        aria-label="Select display option"
        >
        {!displayOpts.has('aod_500nm') && (
            <option value="aod_500nm">aod_500nm</option>
        )}

        {Array.from(displayOpts).map((opt, index) => (
            <option key={index} value={opt}>
            {opt}
            </option>
        ))}
        </Form.Select>
        </div>
        <br/>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'right' }}>
        <Card.Header style={{ fontWeight: 'bold' }}>VALUE FILTER</Card.Header>
        <Form.Select
        style={{ width: "20%" }}
        value={filterSym}
        onChange={handleFilterSym}
        aria-label="Select display option"
        >
        {!displayOpts.has(' ') && (
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
        style={{ marginLeft: '10px', width: '50%' }}
        />
        </div>
        </Modal.Body>
        </Modal>
        </>
    );
};

export default SidePanel;
