# Project presentation

## Final PowerPoint presentation

The final presentation for our Big Data project is available as a [PowerPoint file](Data_Explorers_14_Slide_Presentation.pptx) and on [Google Slides](https://docs.google.com/presentation/d/1qiurnjcADCiUzIlvk-FMd918oSVmURi-/edit?usp=sharing&ouid=117470534552713157665&rtpof=true&sd=true).

## Earlier Quarto draft

The earlier Quarto draft is in `presentation.qmd`, with custom styling in `styles.css`. The final PowerPoint was prepared separately.

### View the Quarto draft

Open the rendered `presentation.html` in a web browser. Keep the accompanying `presentation_files/` folder alongside it if Quarto generated one. If you don’t have the HTML file, follow the render instructions below.

### Edit and render the Quarto draft

1. Install Quarto if you don’t have it.
2. Edit `presentation.qmd` to update the slides or `styles.css` to change their appearance.
3. From the repository root, run:

   ```sh
   quarto render presentation/presentation.qmd
   ```

4. Open `presentation/presentation.html` in your browser. For a live preview while editing, run `quarto preview presentation/presentation.qmd`.

### Why I used Quarto for the draft

I chose Quarto because the slides are easy to write in Markdown and Git makes changes easy to track. The same `.qmd` file can also produce PowerPoint and PDF versions, though their layout and features may differ from the browser version.
