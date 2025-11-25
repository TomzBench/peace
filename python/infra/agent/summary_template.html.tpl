<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    @page {
      size: letter;
      margin: 0.75in 0.75in;
      @bottom-center {
        content: counter(page);
        font-family: system-ui, -apple-system, sans-serif;
        font-size: 9pt;
        color: #888;
      }
    }
    
    * { box-sizing: border-box; }
    
    body {
      font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
      font-size: 11pt;
      line-height: 1.6;
      color: #1a1a1a;
      margin: 0;
      padding: 0;
    }
    
    header {
      background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
      color: white;
      padding: 1.5em;
      margin: -0.75in -0.75in 1.5em -0.75in;
      width: calc(100% + 1.5in);
    }
    
    header h1 {
      font-size: 20pt;
      margin: 0 0 0.3em 0;
      font-weight: 600;
      line-height: 1.3;
    }
    
    .meta {
      color: #a0a0b0;
      font-size: 10pt;
    }
    
    .meta span:not(:last-child)::after {
      content: " · ";
    }
    
    .headline-section {
      background: linear-gradient(135deg, #f8f7ff 0%, #ffffff 100%);
      border-left: 4px solid #6366f1;
      padding: 1.25em 1.5em;
      margin: 0 0 2em 0;
      border-radius: 0 8px 8px 0;
    }
    
    .headline-label {
      text-transform: uppercase;
      font-size: 9pt;
      font-weight: 600;
      color: #6366f1;
      letter-spacing: 0.05em;
      margin-bottom: 0.5em;
    }
    
    .headline-text {
      font-size: 14pt;
      font-weight: 500;
      color: #2d2d44;
      line-height: 1.4;
      margin: 0;
    }
    
    section {
      margin-bottom: 1.75em;
    }
    
    h2 {
      font-size: 13pt;
      font-weight: 600;
      color: #2d2d44;
      margin: 0 0 0.75em 0;
      padding-bottom: 0.4em;
      border-bottom: 2px solid #e8e8f0;
    }
    
    .key-points {
      display: flex;
      flex-direction: column;
      gap: 0.6em;
    }
    
    .point-card {
      background: #f8f8fc;
      padding: 0.9em 1.1em;
      border-radius: 6px;
      border-left: 3px solid #6366f1;
      font-size: 10.5pt;
    }
    
    .point-number {
      color: #6366f1;
      font-weight: 600;
      margin-right: 0.5em;
    }
    
    .concepts-grid {
      display: grid;
      gap: 0.75em;
    }
    
    .concept-item {
      background: #fafafa;
      padding: 0.8em 1em;
      border-radius: 6px;
      border: 1px solid #e8e8f0;
    }
    
    .concept-term {
      font-weight: 600;
      color: #6366f1;
      font-size: 10.5pt;
      margin-bottom: 0.25em;
    }
    
    .concept-def {
      font-size: 10pt;
      color: #444;
      margin: 0;
    }
    
    .narrative {
      text-align: justify;
      font-size: 10.5pt;
      line-height: 1.7;
    }
    
    .narrative p {
      margin: 0 0 1em 0;
    }
    
    .narrative p:last-child {
      margin-bottom: 0;
    }
    
    footer {
      margin-top: 2em;
      padding-top: 1em;
      border-top: 1px solid #e8e8f0;
      font-size: 9pt;
      color: #888;
      text-align: center;
    }
    
    .video-link {
      color: #6366f1;
      text-decoration: none;
    }
  </style>
</head>
<body>
  <header>
    <h1>{{ title }}</h1>
    <div class="meta">
      <span>{{ channel }}</span>
      <span>{{ duration }}</span>
      {% if date %}<span>{{ date }}</span>{% endif %}
    </div>
  </header>
  
  <div class="headline-section">
    <div class="headline-label">Core Thesis</div>
    <p class="headline-text">{{ headline }}</p>
  </div>
  
  <section>
    <h2>Key Takeaways</h2>
    <div class="key-points">
      {% for point in key_points %}
      <div class="point-card">
        <span class="point-number">{{ loop.index }}.</span>{{ point }}
      </div>
      {% endfor %}
    </div>
  </section>
  
  {% if concepts %}
  <section>
    <h2>Key Concepts</h2>
    <div class="concepts-grid">
      {% for concept in concepts %}
      <div class="concept-item">
        <div class="concept-term">{{ concept.term }}</div>
        <p class="concept-def">{{ concept.definition }}</p>
      </div>
      {% endfor %}
    </div>
  </section>
  {% endif %}
  
  <section>
    <h2>Summary</h2>
    <div class="narrative">
      {% for para in narrative %}
      <p>{{ para }}</p>
      {% endfor %}
    </div>
  </section>
  
  <footer>
    {% if video_id %}
    <a class="video-link" href="https://youtube.com/watch?v={{ video_id }}">Watch original video</a> · 
    {% endif %}
    Generated {{ generation_date }}
  </footer>
</body>
</html>
