wagtail_text_alignment
================

**Why is this package better than other implementations?**

Other implementations often lack support for text alignment on block entities.
This package doesn't have that limitation. You can align text, headings, lists, etc.

Quick start
-----------

1. Install the package via pip:

   ```bash
   pip install wagtail_text_alignment
   ```

2. Add 'wagtail_text_alignment' to your INSTALLED_APPS setting like this:

   ```
   INSTALLED_APPS = [
   ...,
      'wagtail_text_alignment',
   ]
   ```

3. Add 'text-alignment' to your richtext features. (it is included in default features)

4. To align it on the frontend too; add the following CSS:

   ```css
   .text-left {
       text-align: left;
   }
   .text-center{
       text-align: center;
   }
   .text-right {
       text-align: right;
   }
   ```
   