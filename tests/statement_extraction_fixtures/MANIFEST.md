# Statement extraction fixtures

Real-world modern slavery statement files pulled from the live CDN
(`https://d1nwpnqfv292tl.cloudfront.net/s3fs-public/statements/`, see
`StatementView::LIVE_CDN`) for use as test fixtures in the markdown/text
extraction package (`MarkdownExtractor`). Selected to cover known problem
cases rather than "typical" statements.

Candidates were found by querying the local `sisc_audit` table for rows
where `modern_slavery_act = ''` (the automated audit could not classify the
document — a reasonable proxy for "extraction previously produced no usable
content"), then fetching and manually inspecting the actual files. A few
clean/readable examples are included as baselines for contrast.

The CDN is CloudFront-backed (S3 origin), independent of the tiscreport.org
Cloudflare proxy, so none of this was affected by the recent Cloudflare change.

## HTML

| File | Company | Issue demonstrated |
|---|---|---|
| `html_aspnet_form_wraps_body_heavy_nav_stihl.html` | Andreas Stihl Ltd (2019-2020) | Legacy ASP.NET WebForms page — the entire visible body, including the real statement content, is wrapped in a single `<form id="ctl01">`. A naive "strip all forms" content filter drops everything. Also has a large multi-level nav menu. |
| `html_bot_challenge_incapsula_no_content.html` | multiple (e.g. Nando's, Copart UK) | Imperva/Incapsula bot-challenge page — body is empty, only a JS challenge script tag. No content is retrievable without executing JS. |
| `html_bot_challenge_distil_captcha_redirect_shearings.html` | Shearings Holidays (2017-2018) | Distil Networks bot-block page: meta-refresh redirect to a captcha URL, no real content. |
| `html_spa_shell_angularjs_no_content_arora.html` | Arora Hotels / Arora Holdings (2015-2016) | AngularJS SPA shell — markup is just `ui-view` placeholders, real content only exists after client-side JS renders it. |
| `html_expired_domain_parking_page_pdr.html` | P.D.R. Construction Ltd (2019-2020) | Original domain expired and now serves a domain-parking / ad page with obfuscated JS, unrelated to the original statement. |
| `html_frameset_embeds_external_pdf_gwalters.html` | G. Walters (Holdings) Ltd (2017-2018) | Old-school `<frameset>` whose single frame points at an external PDF URL. The HTML itself carries no statement text. |
| `html_pdf_flip_viewer_shell_no_content_leonardo.html` | Leonardo Hotel Management (UK) Ltd | "Page flip" JS viewer shell (loads a PDF into a JS widget client-side) — static HTML has no text content. |
| `html_literal_blocking_response.html` | (redacted/anonymised in source data) | Entire response body is the literal string `blocking` — an edge case where the crawler/proxy layer returned an error string instead of a document. |
| `html_broken_link_file_not_found_fr.html` | (French-hosted statement) | Body is just `<b>Fichier inexistant !</b>` — a broken-link/404-style response saved as if it were the statement. |
| `html_cookie_banner_heavy_nav_boilerplate_hilton.html` | Hilton Foods UK Ltd (2019-2020) | ~2MB real corporate page: large multi-level nav (177 nav/menu matches), cookie-consent banner, lots of boilerplate around a real statement. |
| `html_cookie_banner_policy_boilerplate_chanel.html` | Chanel Ltd (2019-2020) | Heavy cookie-consent/legal boilerplate (137 "cookie" mentions) wrapping a general policies page rather than a focused statement. |
| `html_clean_baseline_small_cookie_notice_fidessa.html` | Fidessa Group Holdings Ltd (2015-2016) | Small, clean statement page with just a simple cookie notice banner. Useful as a positive baseline. |

## Images (statement submitted as a raw photo/scan)

| File | Company | Issue demonstrated |
|---|---|---|
| `image_jpg_statement_scan_rothesay.jpg` | Rothesay Life plc / Rothesay Ltd (2016-2017) | Statement file is a JPEG photo/scan of a printed page, not a document format. Requires OCR/image-to-text extraction. |
| `image_png_statement_scan_lockton.png` | Lockton Companies LLP (2015-2016) | Same as above but PNG. |

## PDF

| File | Company | Issue demonstrated |
|---|---|---|
| `pdf_scanned_no_text_layer_south_pennine_academies.pdf` | South Pennine Academies | Genuine scanned PDF: 2 pages, each a full-page JPEG image, zero embedded text layer (confirmed via `pdfimages`/`pdftotext`). Needs OCR. |
| `pdf_garbled_letter_spacing_atkinsrealis.pdf` | AtkinsRéalis UK Ltd / SNC-Lavalin (2019-2020) | Text layer present but font/kerning extraction inserts spurious spaces mid-word (e.g. "SL AVERY", "TR AFFICKING", "L AVALIN"). Classic PDF text-extraction garbling that isn't OCR-related. |
| `pdf_large_image_heavy_annual_report_mondelez.pdf` | Mondelez UK Ltd (2020-2021) | 25-page, ~19.5MB glossy annual-report-style PDF, heavy on design/imagery relative to text. Stress test for large/complex layouts. |
| `pdf_garbled_tounicode_identity_h_regis.pdf` | Regis Resources (Modern Slavery Statement, 6 pages) | Text layer present but decodes to gibberish (e.g. "DŽĚĞƌŶ\x03^ůĂǀĞƌǇ") because the Type0/Identity-H font subsets have a wrong ToUnicode map. Only OCR of the rendered page can read it. |
| `pdf_scanned_rotated_180_crayola.pdf` | Binney & Smith (Europe) Ltd / Crayola (2019) | One-page scan stored upside down, with the page rotated 180° for display. OCR of the raw embedded image reads gibberish; only the rendered page reads the right way up. |
| `pdf_scanned_rotated_270_two_pages.pdf` | NewRiver REIT plc | Two-page landscape scan stored sideways, pages rotated 270° for display. Same problem as the Crayola fixture. |

## Word / PowerPoint

| File | Company | Issue demonstrated |
|---|---|---|
| `doc_legacy_binary_format_emr.doc` | EMR (EMR Safety Policy) | Legacy binary (pre-2007) `.doc` format. |
| `docx_clean_baseline_pdq_distribution.docx` | P.D.Q. Distribution Ltd | Clean, modern `.docx` with genuine extractable statement text. Positive baseline. |
| `docx_content_is_embedded_image_no_text_brightsun.docx` | Brightsun Travel (UK) Ltd / Maxxima Ltd / Indigo Parent Ltd (2018-2019 / 2021-2022) | `.docx` whose entire body is a single embedded picture (`word/document.xml` contains one `<w:drawing>`, no text runs). Needs OCR of the embedded image, not text extraction. |
| `ppt_extension_mismatch_actually_word_doc_wrong_content_tangent.ppt` | Tangent International Ltd/Group (2016-2017) | File has a `.ppt` extension but is actually a binary Word `.doc` (confirmed via `file`), and its content ("Standard Handbook") isn't a modern slavery statement at all — likely the wrong file was uploaded. Covers both extension/content-type mismatch and wrong-document-uploaded cases. Note: no genuine PowerPoint-format statement could be found in the live dataset — every `.ppt`-extensioned file sampled turned out to be a mislabelled Word document. |

## Notes for whoever writes the tests

- Several of the "no content" HTML cases (SPA shells, bot challenges, frameset,
  PDF-flip viewer) are legitimately un-extractable from static HTML alone —
  the test suite should assert graceful/empty handling rather than expect
  real text.
- The `.ppt` finding suggests it may be worth having the extractor sniff
  actual file type/magic bytes rather than trusting the extension, since this
  is not a one-off in the live dataset.
