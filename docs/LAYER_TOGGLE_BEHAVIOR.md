# Paraguay Geodata — Layer Toggle Behavior

**Live:** https://geodata.paragu-ai.com/

All 31 toggleable layers (8 groups, 7 sub-groups) behave correctly when the user turns them off. The property cluster view is filtered by active sub-layers in real time.

## Sub-layer filtering (the trickiest case)

The real-estate group has 7 sub-layers: 3 by listing type (`sale`, `rent`, `short_rent`) and 4 by property type (`house`, `apartment`, `land`, `commercial`). Each property marker is registered in BOTH its listing-type group and its property-type group (dual registration). A marker is visible when **either** its listing-type sub-layer **or** its property-type sub-layer is active.

### How it's enforced

`clusterProperties(features)` filters before rendering:

```js
const activeListing = {
    sale:      layerState.properties_sale.active,
    rent:      layerState.properties_rent.active,
    short_rent: layerState.properties_short.active,
};
const activeType = {
    house:      layerState.properties_house.active,
    apartment:  layerState.properties_apartment.active,
    land:       layerState.properties_land.active,
    commercial: layerState.properties_commercial.active,
};
const anyActive = Object.values(activeListing).some(Boolean) || Object.values(activeType).some(Boolean);
if (!anyActive) return;  // no markers at all
const visibleFeatures = features.filter(f => {
    const p = f.properties;
    const lt = p.listing_type === 'short_rent' ? 'short_rent' : p.listing_type;
    const pt = p.property_type;
    return activeListing[lt] === true || activeType[pt] === true;
});
```

`applyLayerVisibility(id)` triggers `clusterProperties()` re-run whenever a property sub-layer is toggled, so the cluster view stays in sync.

## Heatmap legend behavior

When the user toggles a heatmap layer:
- ON: layer added to map, legend refreshed (or created if first heatmap)
- OFF: layer removed from map, legend re-rendered (or hidden if no heatmaps left)

The legend is recreated fresh each time so it shows only the rows for currently-active heatmaps.

## Test

`/tmp/test_toggle_quick.js` exercises 12 scenarios with assertions:

| # | State | Expected | Actual |
|---|---|---|---|
| 1 | only sale ON | 6 | 6 ✓ |
| 2 | only house ON | 4 | 4 ✓ |
| 3 | sale + house (union) | 7 | 7 ✓ |
| 4 | all OFF | 0 | 0 ✓ |
| 5 | house + rent | 6 | 6 ✓ |
| 6 | only land ON | 2 | 2 ✓ |
| 7 | only short_rent ON | 1 | 1 ✓ |
| 8 | only commercial ON | 1 | 1 ✓ |
| 9 | only apartment ON | 3 | 3 ✓ |
| 10 | only rent ON | 3 | 3 ✓ |
| 11 | all 7 ON | 10 | 10 ✓ |
| 12 | sale + rent (cross) | 9 | 9 ✓ |

12/12 pass.

## Other layers

The remaining 24 layers (catastro, INBIO, OSM, biodiversity, etc.) use the standard pattern:
- Each has its own `LAYER_GROUPS[id][0]` group.
- The loader fills the group with markers/polygons.
- `applyLayerVisibility(id)` adds/removes the group from the map.
- The single `tile_fabric` (7,912 cells) layer uses one Leaflet group for all rectangles; toggling off hides them all.
- Each INBIO crop (`inbio_soja`, `inbio_arroz`, `inbio_maiz`) has its own group.

No dual registration, no shared group state.

## Edge cases handled

1. **Toggle all property sub-layers off** → cluster returns early, map shows no property markers
2. **Heatmap all off** → legend element removed from DOM
3. **Heatmap pha + risk both on, then pha off** → legend re-rendered showing only risk row
4. **Cluster at zoom >= 11** with cap of 1,500 markers; "more" indicator shows overage
5. **Re-cluster on zoom** (zoomend handler) now respects sub-layer state