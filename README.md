# Rebuilding State of the Child and Housing Information Portal

We're rebuilding the State of the Child and the Housing Information Portal applications to make them easier to maintain. We're removing the dependence on an external API and bringing everything from the application onto two singular boxes, one for HIP and one for SDC. This document describes how we're going to go about that work.

## The new State of the Child profile schema

This section will explain most of the tables that are used to create the profile and make sure the application has the right information specified to successfully draw the profiles.

### Locations

This is dependent on our [geographies](https://github.com/data-driven-detroit/geographies) ETL.

Locations includes a few different tables

- `location` The main table that holds all the geographies to which we're aggregating.
- `location_type` The types of geographies that are available on the tool.
- `location_type_parent_location_types` Relates the various location types to tell the app which comparisons to draw.

The schema for each of these is available in the data\_dictionaries folder.

### Page organization

Broadly, the SDC profile is organized into sections and categories (rows). Each of these has a table that allows them to supply 'about' text and a permalink.

- `section` 'sections' are the large page divisions.
- `category` 'categories' are the rows.

### Indicators

- `indicator` This is the table that holds all of the information about constructing the indicators themselves. To distinguish this information from the `indicator_data_visual` table, remember that the same data can be shown with different visualizations, say either a bar chart or doughnut. The data visual table allows you to describe how you want the indicator to be shown where the indicator table describes what the indicator is.
- `indicator_data_visual` See above, this table holds the info describing what the indicator should look like on the page.
- `indicator_filter_option` The categories that indicator data is broken into. For instance percentages in a doughnut chart will each have their own row in the `indicator_value` table, but you can provide the filter option to identify which portion of the chart the value corresponds to. For instance, 'male' and 'female.'
- `indicator_filter_type` A helper to categorize filter options into coherent groups like gender, age ranges, income ranges, etc.
- `indicator_source` The table that holds sources of the indicator data
- `indicator_value` The data table for the application SEE BELOW FOR DETAILS
- `color_scale` TODO (Mike): Figure out how this works

#### The `indicator_value` table

The `indicator_value` table is the central table in the system. It's has keys to several of the other tables that all need to be filled in correctly to successfully draw the visualization. The fields are described in a data dictionary in the 'data\_dictionaries' directory, but I've repeated some of those descriptions here:

- `id` A unique id for each row of this table
- `start_date` The start date for when the data is valid. For example, the ACS 2023 5-year would have a start date of 2019-01-01. Data points that correspond to a year should have January first as the start date and December 31st as the end date. If the dataset only makes sense as a point -- then you can make the `start_date` and `end_date` the same.
- `end_date` The end date for when the data is valid. For example, the ACS 2023 5-year would have a start date of 2023-12-31. The end date takes priority on the chart axis.
- `value` This is the value that will display on the profile for this filter and indicator. The 'type' of value this is set on the indicator table so whether this is a rate, median, percentage, etc, the published value will appear here. 
- `value_moe` The margin of error for the value field.
- `count` When aggregating some indicator types, we need to keep track of the values that compose the result. The simplest example would be for percentages where 'count' would be the numerator and 'universe' would be the denominator. In other cases, like averages, we would use 'value' in conjunction with count to produce a weighted average. TODO (Mike): double check this behavior.
- `count_moe` The margin of error for the count.
- `universe` The denominator for percentages and rates, so we can easily combine them in custom geographies.
- `universe_moe` The margin of error for the universe.
- `filter_option_id` Take a look at the filter option data dictionary file for more information, but a lot of indicators are made up of several values that work together, for instances the components of a doughnut chart. Each slice of the doughnut has its own 'filter option' and that is set in this field. The `indicator_filter_option` table holds all of these options and this id corresponds to an entry in that table.
- `indicator_id` An indicator may be made up of several values (organized with filters) this field holds the id of the indicator this value is a part of.
- `source_id` An indicator may be the same for multiple years, but the source of the data will change over time, at least in publish date, e.g. you can get population numbers for ACS 2021 5-Year then update to ACS 2023 5-Year, and the only thing that needs to change is the date
- `location_id` The id for the row in the `location` table that the value is associated with. 

## How we're going to create these tables

There are three directories with tables that must be filled out to capture the profile structure of HIP and SDC. Two of them are labeled, 'hip' and 'sdc.' The Third is labeled 'shared.' The 'shared' directory has tables that relate to locations. These tables should be identical between HIP and SDC so there is no need to have separate source files. Our goal is to completely fill out all of these files.

### Profile structure tables

For every table besides the `location` table and the `indicator_value` table, we'll create these mostly by hand. These are easier to create, and many are already complete. Review the data dictionaries for each of these tables and then walk through the SDC and HIP profiles recording all sections, categories, and indicator titles, qualifiers, ands filter. Collect any issues that you find or questions in the corresponding ETL board for HIP or SDC on Asana.

### Values table ETL

This requires us to revise our SDC / HIP ETL scripts to match the schema of the `indicator_value` table. See our NVI ETL code for reference. The strategy has been to proceed like we normally do, creating a 'wide' table where each location has values on the columns, then as a final step we transform the dataset to 'tall' format. Each column in the 'wide' format has a corresponding `indicator_id` and `filter_option_id` in the 'tall' format. The values, counts, universes and their respective MOEs are placed in 
