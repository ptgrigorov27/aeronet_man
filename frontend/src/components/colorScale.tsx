import React, { useState, useEffect } from 'react';
import { Box, Typography, Grid } from '@mui/material';
import * as d3 from 'd3-scale';
import {Tooltip, OverlayTrigger } from 'react-bootstrap';

interface ColorLegendProps {
  type: string,
  activateTrace: boolean;
}
const ColorLegend: React.FC<ColorLegendProps> = ({type, activateTrace}) => {
  let markerDomain: number[] = [];
  let markerTicks: number[] = [];
  let traceDomain: number[] = [0, 5];
  let traceTicks: number[] = [0, 2.5, 5];
  const [traceActive, setTraceActive] = useState(false);


  useEffect(() => {
      //console.log("colorLegend: "+ activateTrace)
    setTraceActive(activateTrace ? true : false);
  }, [activateTrace]);

if (type.includes("std") || type.includes("aod")) {
    markerDomain = Array.from({ length: 6 }, (_, i) => parseFloat((i * 0.1).toFixed(1)));
    markerTicks = markerDomain;  
} else if (type.includes("water") || type.includes("air_mass")) {
    markerDomain = Array.from({ length: 6 }, (_, i) => i);
    markerTicks = markerDomain;
} else if (type.includes("angstrom")) {
    markerDomain = Array.from({ length: 6 }, (_, i) => parseFloat((i * (2 / 5)).toFixed(1)));
    markerTicks = markerDomain;
} else {
    markerDomain = Array.from({ length: 6 }, (_, i) => parseFloat((i / 6).toFixed(1)));
    markerTicks = markerDomain;
}

  const markerScale = d3.scaleLinear<string>()
    .domain(markerDomain)
    .range(["blue", "teal", "green", "yellow", "orange", "red"]);

  const traceScale = d3.scaleLinear<string>()
    .domain(traceDomain)
    .range(["#39FF14", "red"]);

  const gradientColors = markerDomain.map(value => markerScale(value)).join(', ');

 const tickPositions = markerTicks.map((_, index) => {
    const percentagePosition = (index / (markerTicks.length - 1)) * 100;
 
      return `${percentagePosition}%`;
 }); 


 return (
    <Box
      sx={{
        position: 'absolute',
        bottom: '16px',
        left: '16px',
        zIndex: 1000,
        pointerEvents: 'auto',
        width: '320px',
        padding: '5px',
        backgroundColor: 'rgba(255,255,255,0.8)',
        borderRadius: '8px',
        boxShadow: '0 0 5px rgba(0, 0, 0, 0.5)',
        textAlign: 'center',
      }}
    >
      <Typography variant="body1" sx={{ marginBottom: '-12px', fontSize:"0.9em" }}>
        Measurement: <strong>{type.toUpperCase().replace(/_/g, ' ').replace("NM","nm")}</strong>
      </Typography>
      <hr/>
      <OverlayTrigger
        placement="top"
        overlay={<Tooltip id="tooltip-top">Marker Scale</Tooltip>}
      >
        <Box
          sx={{
            marginTop: '8px',
            height: '12px',
            width: '280px',
            backgroundImage: `linear-gradient(to right, ${gradientColors})`,
            border: '0.2px solid #333',
            margin: '0 auto',
            position: 'relative',
            alignContent: 'center',
          }}
        >
          <Box
            sx={{
              position: 'absolute',
              top: '1px',
              left: '-10px',
              width: '0',
              height: '0',
              borderLeft: '5px solid transparent',
              borderRight: '5px solid transparent',
              borderBottom: '8px solid grey',
              transform: 'rotate(-90deg)',
            }}
          />
          <Box
            sx={{
              position: 'absolute',
              top: '1px',
              right: '-10px',
              width: '0',
              height: '0',
              borderLeft: '5px solid transparent',
              borderRight: '5px solid transparent',
              borderBottom: '8px solid darkred',
              transform: 'rotate(90deg)',
            }}
          />
        </Box>
      </OverlayTrigger> 

        <Grid container justifyContent="center" sx={{  width: '100%' }}>
        <Grid container justifyContent="space-between" sx={{ marginTop: '16px', width: '90%' }}>
          {markerTicks.map((tick, index) => (
            <Grid item key={index} sx={{ position: 'relative', textAlign: 'right' }}>
              <Box
                sx={{
                  position: 'absolute',
                  top: '-16px',
                  left: tickPositions[index],
                  width: '1px',
                  height: '5px',
                  backgroundColor: "black",
                }}
              />
            </Grid>
          ))}
        </Grid>
        </Grid>
        <Grid container justifyContent="center" sx={{width: '100%'}}>
        <Grid container justifyContent="space-between" sx={{marginTop: '0px', width: '100%' }}>
          {markerTicks.map((tick, index) => (
            <Grid item key={index} sx={{ position: 'relative', textAlign: 'center',         width: `calc(${parseFloat(tickPositions[1]) / 2}%)` }}>
              <Typography variant="caption" sx={{ position: 'relative', top: '-8px',fontWeight: 'bold', fontSize: '0.75rem', textTransform: 'uppercase'  }}>
                {tick === 0 ? "0.0": tick}
              </Typography>
            </Grid>
          ))}
        </Grid>
        </Grid>
     { traceActive && (<>
      <OverlayTrigger
        placement="top"
        overlay={<Tooltip id="tooltip-top">Cruise Path</Tooltip>}
      >
        <Box
          sx={{
            marginTop: '16px',
            height: '9px',
            width: '300px',
            backgroundImage: `linear-gradient(to right, ${traceScale(traceDomain[0])}, ${traceScale(traceDomain[1])})`,
            border: '1px solid #333',
            margin: '0 auto',
            position: 'relative',
          }}
        />
      </OverlayTrigger>

      <Grid container justifyContent="space-between"   sx={{ width: '300px', marginTop: '20px', margin: '0 auto' }}>
  <Typography 
    sx={{ fontWeight: 'bold', fontSize: '0.75rem', textTransform: 'uppercase' }}
  >
    start
  </Typography>
  <Typography 
    sx={{ fontWeight: 'bold', fontSize: '0.75rem', textTransform: 'uppercase' }}
  >
    end
  </Typography>
      </Grid>   
      </>)}
    </Box>
  );
};

export default ColorLegend;

