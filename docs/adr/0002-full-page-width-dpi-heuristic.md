# Estimate image DPI from page width, not placement geometry

We considered walking each page's content stream to track the CTM and compute an image's true displayed size, but picked a simpler heuristic: assume every image is displayed at the page's full MediaBox width, and compute effective DPI as `pixel_width / page_width_inches`.

This is deliberately conservative in one direction only: if an image is actually placed smaller than full page width, its true effective DPI is higher than the heuristic reports, so the heuristic can only *underestimate* DPI — biasing toward downsampling less aggressively than a precise calculation would allow, never toward degrading an image below the target DPI at its real displayed size. That match to the "Visually Lossless never degrades quality" guarantee is why the simpler heuristic was acceptable; full CTM tracking would only improve compression ratio on non-full-page image placements, not correctness.
