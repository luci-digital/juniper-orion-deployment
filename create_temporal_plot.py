#!/usr/bin/env python3
"""
Create temporal plot of map locations using longitude/latitude,
with colors for temporal progression and ghost artifacts showing drift.
"""

import json
import os
import re
from collections import defaultdict
from datetime import datetime
import math

# Try to import visualization libraries
try:
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    from matplotlib.patches import Circle
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available, will generate data only")

try:
    import folium
    from folium import plugins
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
    print("Warning: folium not available, will use matplotlib only")

class TemporalLocationPlotter:
    def __init__(self, organized_maps_file='data/organized_maps.json'):
        self.organized_maps_file = organized_maps_file
        self.locations = []
        
        # Common location coordinates (we'll geocode place names)
        self.location_coords = {
            # Countries
            'europe': (10.0, 50.0),
            'asia': (100.0, 35.0),
            'africa': (20.0, 0.0),
            'america': (-100.0, 40.0),
            'germany': (10.5, 51.5),
            'france': (2.2, 46.2),
            'spain': (-3.7, 40.4),
            'italy': (12.5, 41.9),
            'austria': (13.3, 47.5),
            'hungary': (19.5, 47.5),
            'netherlands': (5.3, 52.1),
            'belgium': (4.4, 50.5),
            'switzerland': (8.2, 46.8),
            'poland': (19.1, 52.2),
            'romania': (24.9, 45.9),
            'uk': (-1.0, 52.0),
            'usa': (-98.6, 39.8),
            'china': (104.2, 35.9),
            'japan': (138.6, 36.2),
            'india': (77.2, 28.6),
            'brazil': (-47.9, -15.8),
            'russia': (37.6, 55.8),
            'kazakhstan': (66.9, 48.0),
            'madagascar': (46.7, -18.9),
            'indonesia': (113.9, -0.8),
            'balkans': (20.0, 44.0),
            'holy land': (35.2, 31.8),
            # Cities
            'paris': (2.3, 48.9),
            'vienna': (16.4, 48.2),
            'budapest': (19.0, 47.5),
            'linz': (14.3, 48.3),
            'luxembourg': (6.1, 49.6),
            'antwerp': (4.4, 51.2),
            'chieti': (14.2, 42.4),
            'luhansk': (39.3, 48.6),
            'prague': (14.4, 50.1),
            'machakos': (37.3, -1.5),
            'weehawken': (-74.0, 40.8),
            'lučenec': (19.7, 48.3),
            'karaganda': (73.1, 49.8),
            'colorado': (-105.3, 39.0),
            'southeast asia': (110.0, 5.0),
            'siberia': (100.0, 60.0),
            'japan': (138.6, 36.2),
            'madeira': (-16.9, 32.7),
            'pyrenees': (1.0, 42.7),
            'ocean indien': (60.0, -20.0),
            'são paulo': (-46.6, -23.6),
            'kenya': (37.9, -0.0),
            'iran': (53.7, 32.4),
        }
    
    def geocode_location(self, text):
        """Extract location and get coordinates from text."""
        if not text:
            return None
        
        text_lower = text.lower()
        
        # Try to find known locations
        for location, coords in self.location_coords.items():
            if location in text_lower:
                return {
                    'name': location.title(),
                    'longitude': coords[0],
                    'latitude': coords[1],
                    'confidence': 'high' if len(location) > 5 else 'medium'
                }
        
        # Try to extract coordinates directly (if present)
        coord_pattern = r'(-?\d+\.?\d*)[°\s,]+(-?\d+\.?\d*)'
        match = re.search(coord_pattern, text)
        if match:
            try:
                lon = float(match.group(1))
                lat = float(match.group(2))
                # Validate reasonable ranges
                if -180 <= lon <= 180 and -90 <= lat <= 90:
                    return {
                        'name': 'Coordinates',
                        'longitude': lon,
                        'latitude': lat,
                        'confidence': 'high'
                    }
            except ValueError:
                pass
        
        return None
    
    def extract_locations_from_maps(self):
        """Extract locations and temporal data from organized maps."""
        print("Loading organized maps data...")
        with open(self.organized_maps_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        maps = data.get('maps', [])
        print(f"Processing {len(maps)} maps for location data...")
        
        locations = []
        
        for map_data in maps:
            filename = map_data.get('filename', '')
            dates = map_data.get('dates', [])
            chronological_date = map_data.get('chronological_date', 0)
            regions = map_data.get('geographic_regions', [])
            captions = map_data.get('captions', {})
            
            # Get all text that might contain location info
            location_texts = []
            location_texts.extend(regions)
            for lang, caption in captions.items():
                location_texts.append(caption)
            location_texts.append(filename)
            
            # Try to geocode
            for text in location_texts:
                location = self.geocode_location(text)
                if location:
                    # Use the best date available
                    date = chronological_date if chronological_date > 0 else (dates[0] if dates else 0)
                    
                    locations.append({
                        'map_filename': filename,
                        'location_name': location['name'],
                        'longitude': location['longitude'],
                        'latitude': location['latitude'],
                        'date': date,
                        'dates': dates,
                        'confidence': location['confidence'],
                        'source_text': text[:100]
                    })
                    break  # Use first successful geocoding
        
        self.locations = locations
        print(f"Extracted {len(locations)} locations with coordinates")
        return locations
    
    def create_matplotlib_plot(self):
        """Create temporal plot using matplotlib."""
        if not MATPLOTLIB_AVAILABLE:
            print("Matplotlib not available, skipping plot generation")
            return None
        
        if not self.locations:
            print("No locations to plot")
            return None
        
        # Filter valid locations
        valid_locations = [loc for loc in self.locations if loc['date'] > 0]
        if not valid_locations:
            print("No locations with valid dates")
            return None
        
        # Sort by date
        valid_locations.sort(key=lambda x: x['date'])
        
        # Get date range for color mapping
        dates = [loc['date'] for loc in valid_locations]
        min_date = min(dates)
        max_date = max(dates)
        date_range = max_date - min_date if max_date > min_date else 1
        
        # Create figure
        fig, ax = plt.subplots(figsize=(16, 10))
        
        # Create colormap for temporal progression
        try:
            # Try new matplotlib API first
            cmap = plt.colormaps['viridis']
        except (AttributeError, KeyError):
            # Fallback to old API
            try:
                cmap = cm.get_cmap('viridis')
            except AttributeError:
                cmap = plt.cm.viridis
        
        # Plot ghost artifacts (historical positions with transparency)
        for i, loc in enumerate(valid_locations):
            # Calculate alpha based on temporal distance from most recent
            temporal_distance = (loc['date'] - min_date) / date_range
            alpha = 0.2 + (temporal_distance * 0.6)  # Older = more transparent (ghost effect)
            
            # Color based on date
            color = cmap(temporal_distance)
            
            # Plot ghost marker (larger, more transparent)
            ax.scatter(loc['longitude'], loc['latitude'], 
                      s=200, alpha=alpha*0.5, c=[color], 
                      edgecolors='none', marker='o', zorder=1)
            
            # Plot main marker (smaller, more opaque)
            ax.scatter(loc['longitude'], loc['latitude'],
                      s=50, alpha=min(alpha + 0.3, 1.0), c=[color],
                      edgecolors='black', linewidths=0.5, marker='o', zorder=2)
        
        # Draw drift lines connecting temporally adjacent points
        for i in range(len(valid_locations) - 1):
            loc1 = valid_locations[i]
            loc2 = valid_locations[i + 1]
            
            # Only draw if locations are reasonably close (same region)
            distance = math.sqrt(
                (loc1['longitude'] - loc2['longitude'])**2 + 
                (loc1['latitude'] - loc2['latitude'])**2
            )
            
            if distance < 50:  # Within reasonable distance
                temporal_dist = (loc1['date'] - min_date) / date_range
                alpha = 0.1 + (temporal_dist * 0.3)
                color = cmap(temporal_dist)
                
                ax.plot([loc1['longitude'], loc2['longitude']],
                       [loc1['latitude'], loc2['latitude']],
                       color=color, alpha=alpha, linewidth=1, linestyle='--', zorder=0)
        
        # Add labels for key locations
        unique_locations = {}
        for loc in valid_locations:
            key = (loc['longitude'], loc['latitude'])
            if key not in unique_locations or loc['date'] > unique_locations[key]['date']:
                unique_locations[key] = loc
        
        for loc in list(unique_locations.values())[:20]:  # Limit labels
            ax.annotate(loc['location_name'], 
                       (loc['longitude'], loc['latitude']),
                       xytext=(5, 5), textcoords='offset points',
                       fontsize=8, alpha=0.7)
        
        # Add colorbar
        sm = plt.cm.ScalarMappable(cmap=cmap, 
                                   norm=plt.Normalize(vmin=min_date, vmax=max_date))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax)
        cbar.set_label('Year', rotation=270, labelpad=20)
        
        # Set labels and title
        ax.set_xlabel('Longitude', fontsize=12)
        ax.set_ylabel('Latitude', fontsize=12)
        ax.set_title('Temporal Progression of Map Locations\n(Ghost artifacts show historical positions)', 
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Set reasonable bounds
        lons = [loc['longitude'] for loc in valid_locations]
        lats = [loc['latitude'] for loc in valid_locations]
        ax.set_xlim(min(lons) - 5, max(lons) + 5)
        ax.set_ylim(min(lats) - 5, max(lats) + 5)
        
        # Save figure
        output_file = 'chronology/temporal_location_plot.png'
        os.makedirs('chronology', exist_ok=True)
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Matplotlib plot saved: {output_file}")
        
        plt.close()
        return output_file
    
    def create_folium_map(self):
        """Create interactive temporal map using Folium."""
        if not FOLIUM_AVAILABLE:
            print("Folium not available, skipping interactive map")
            return None
        
        if not self.locations:
            print("No locations to plot")
            return None
        
        valid_locations = [loc for loc in self.locations if loc['date'] > 0]
        if not valid_locations:
            print("No locations with valid dates")
            return None
        
        valid_locations.sort(key=lambda x: x['date'])
        
        # Calculate center
        lons = [loc['longitude'] for loc in valid_locations]
        lats = [loc['latitude'] for loc in valid_locations]
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)
        
        # Create base map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=3)
        
        # Get date range for color mapping
        dates = [loc['date'] for loc in valid_locations]
        min_date = min(dates)
        max_date = max(dates)
        date_range = max_date - min_date if max_date > min_date else 1
        
        # Create feature groups for different time periods
        time_groups = defaultdict(list)
        for loc in valid_locations:
            # Group by century
            century = (loc['date'] // 100) * 100
            time_groups[century].append(loc)
        
        # Color palette
        colors = ['#440154', '#31688e', '#35b779', '#fde725']  # viridis-like
        
        # Add markers with ghost effects
        for i, loc in enumerate(valid_locations):
            temporal_dist = (loc['date'] - min_date) / date_range
            
            # Determine color
            color_idx = min(int(temporal_dist * len(colors)), len(colors) - 1)
            color = colors[color_idx]
            
            # Calculate opacity (ghost effect - older = more transparent)
            opacity = 0.3 + (temporal_dist * 0.7)
            
            # Create popup text
            popup_text = f"""
            <b>{loc['location_name']}</b><br>
            Map: {loc['map_filename'][:30]}...<br>
            Date: {loc['date']}<br>
            Source: {loc['source_text'][:50]}...
            """
            
            # Add marker
            folium.CircleMarker(
                location=[loc['latitude'], loc['longitude']],
                radius=8,
                popup=folium.Popup(popup_text, max_width=300),
                color=color,
                fillColor=color,
                fillOpacity=opacity,
                weight=2,
                tooltip=f"{loc['location_name']} ({loc['date']})"
            ).add_to(m)
            
            # Add ghost marker (larger, more transparent)
            folium.CircleMarker(
                location=[loc['latitude'], loc['longitude']],
                radius=15,
                popup=None,
                color=color,
                fillColor=color,
                fillOpacity=opacity * 0.3,
                weight=1,
            ).add_to(m)
        
        # Add lines showing temporal drift
        for i in range(len(valid_locations) - 1):
            loc1 = valid_locations[i]
            loc2 = valid_locations[i + 1]
            
            distance = math.sqrt(
                (loc1['longitude'] - loc2['longitude'])**2 + 
                (loc1['latitude'] - loc2['latitude'])**2
            )
            
            if distance < 50:  # Only connect nearby points
                temporal_dist = (loc1['date'] - min_date) / date_range
                color_idx = min(int(temporal_dist * len(colors)), len(colors) - 1)
                color = colors[color_idx]
                opacity = 0.2 + (temporal_dist * 0.3)
                
                folium.PolyLine(
                    locations=[[loc1['latitude'], loc1['longitude']],
                              [loc2['latitude'], loc2['longitude']]],
                    color=color,
                    weight=2,
                    opacity=opacity,
                    dashArray='5, 5'
                ).add_to(m)
        
        # Add timeline control
        plugins.TimestampedGeoJson(
            {
                'type': 'FeatureCollection',
                'features': [
                    {
                        'type': 'Feature',
                        'geometry': {
                            'type': 'Point',
                            'coordinates': [loc['longitude'], loc['latitude']]
                        },
                        'properties': {
                            'time': f"{loc['date']}-01-01",
                            'name': loc['location_name'],
                            'popup': f"{loc['location_name']} ({loc['date']})"
                        }
                    }
                    for loc in valid_locations
                ]
            },
            period='P10Y',  # 10 year periods
            duration='P5Y',
            add_last_point=True
        ).add_to(m)
        
        # Save map
        output_file = 'chronology/temporal_location_map.html'
        os.makedirs('chronology', exist_ok=True)
        m.save(output_file)
        print(f"Interactive Folium map saved: {output_file}")
        
        return output_file
    
    def generate(self):
        """Generate temporal location plots."""
        print("="*60)
        print("TEMPORAL LOCATION PLOT GENERATION")
        print("="*60)
        print()
        
        # Extract locations
        locations = self.extract_locations_from_maps()
        
        if not locations:
            print("No locations found to plot")
            return
        
        # Save location data
        output_data = {
            'locations': locations,
            'total_locations': len(locations),
            'locations_with_dates': len([l for l in locations if l['date'] > 0]),
            'date_range': {
                'min': min([l['date'] for l in locations if l['date'] > 0] or [0]),
                'max': max([l['date'] for l in locations if l['date'] > 0] or [0])
            }
        }
        
        data_file = 'data/temporal_locations.json'
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"Location data saved: {data_file}")
        
        # Create plots
        results = {}
        
        if MATPLOTLIB_AVAILABLE:
            print("\nCreating matplotlib plot...")
            plot_file = self.create_matplotlib_plot()
            if plot_file:
                results['matplotlib_plot'] = plot_file
        
        if FOLIUM_AVAILABLE:
            print("\nCreating interactive Folium map...")
            map_file = self.create_folium_map()
            if map_file:
                results['folium_map'] = map_file
        
        print(f"\n{'='*60}")
        print("Temporal Location Plot Generation Complete!")
        print(f"  Locations extracted: {len(locations)}")
        print(f"  Locations with dates: {len([l for l in locations if l['date'] > 0])}")
        if results:
            print(f"  Output files: {list(results.values())}")
        
        return results

if __name__ == '__main__':
    plotter = TemporalLocationPlotter()
    plotter.generate()

