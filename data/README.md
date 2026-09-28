# Local Chandrayaan-2 data

Place the extracted ISRO/PRADAN products in this directory. Raw products are
excluded from Git because the collection is several gigabytes and remains the
property of its data providers.

The current evaluation uses these product families:

- OHRC: `ch2_ohr_ncp_20210402T0546284043_d_img_d18`
- OHRC: `ch2_ohr_ncp_20230820T0559124374_d_img_n18`
- OHRC: `ch2_ohr_ncp_20240330T0035085365_d_img_d18`
- TMC-2 fore: `ch2_tmc_ncf_20191208T0221109733_d_img_gds`
- TMC-2 nadir: `ch2_tmc_ncn_20191208T0221109733_d_img_gds`
- IIRS: `ch2_iir_nri_20200109T0733065684_d_img_gds`

Each extracted product should retain its PDS4 label and image/quantum file.
After copying the data, run `python scripts/build_scenarios.py` from the project
root to create the local scenario catalogue.

Do not commit the raw products, extracted image files, or generated scenario
tiles.
