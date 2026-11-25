# Project presentation

This folder contains the Quarto slides for our Big Data project. The slide content is in `presentation.qmd`, and the custom styling is in `styles.css`.

## View the slides

Open the rendered `presentation.html` in a web browser. Keep the accompanying `presentation_files/` folder alongside it if Quarto generated one. If you don’t have the HTML file, follow the render instructions below.

## Edit and render

1. Install Quarto if you don’t have it.
2. Edit `presentation.qmd` to update the slides or `styles.css` to change their appearance.
3. From the repository root, run:

   ```sh
   quarto render presentation/presentation.qmd
   ```

4. Open `presentation/presentation.html` in your browser. For a live preview while editing, run `quarto preview presentation/presentation.qmd`.

## Justification for using Quarto

I chose Quarto because the slides are easy to write in Markdown and Git makes changes easy to track. The same `.qmd` file can also produce PowerPoint and PDF versions, though their layout and features may differ from the browser version.
