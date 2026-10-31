# Supplied descriptions for v06

`m01.md` through `m06.md` preserve the complete description text from the corresponding assistant replies in the fixture-preparation conversation, excluding the thumbnail embeds. Wording, paragraph order, punctuation, and the comic title's Markdown emphasis are retained, with a final newline in each file. These are the descriptions handed off for image generation; they have not been revised to fit the returned images.

The user supplied one selected generation per description with the request to incorporate them into this kit. `../v06-imports.json` maps the original source, prompt, and supplied output by exact path and SHA-256, and retains the uploaded filenames.

The generation service's exact model/version, seed, settings, internal prompt rewriting, full session instructions, and attempt/selection history are not recorded here. Do not fill them in by inference. The recorded text is the visible description prompt, not a claim to reproduce an unseen service request.

The local fixture build imports these outputs unchanged. It does not run these prompts, rewrite them, repair the images, or use them to generate further variants.
