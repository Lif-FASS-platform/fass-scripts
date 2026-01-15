timestamp = "2025-10-25"
number = 2

vab_endpoints = [
    "/atc",
    "/atc?levelBelowAtcCode=N02BF02",
    "/atc?medicineShortageAdviceId",
    "/organization/2058",
]

dab_endpoints = [
    "/atc",
    "/atc?levelBelowAtcCode=QN02BF02",
    "/atc?medicineShortageAdviceId",
    "/organization/2058",
    "/offline/details",
]

vet_npl_id = "20000225000063"
vet_endpoints = [
    "/vet/package/barcode/09006240025231",
    "/vet/medicinal-product?atcCode=QP53AC04",
    "/medicinal-product?fassOrganizationId=2058",
    "/vet/species/atc/QP53",
    "/vet/species/all",
    # ---
    "/applicable-for?nplPackId=20080820100269",
    f"/applicable-for?nplId={vet_npl_id}",
    # ---
    "/atc/top-level",
    "/atc/QN02BF02",
    "/atc?levelBelowAtcCode=QN02BF02",
    "/atc?medicineShortageAdviceId=ee83de64bd0532e94551c0818312a00d",
    # ---
    f"/substance/all?number={number}",
    f"/substance/changelog?timestamp={timestamp}",
    # ---
    "/medicinal-product?atcGroup=QA01",
    "/medicinal-product?atcCode=QP53AB03",
    "/medicinal-product?fassOrganizationId=2336&substanceId=IDE4POESUAGPUVERT1",
    "/medicinal-product?substanceId=IDE4POESUAGPUVERT1",
    "/medicinal-product?fassOrganizationId=2336",
    "/medicinal-product?nplPackId=20080820100269",
    "/medicinal-product/20030402000074",
    "/medicinal-product/20030402000074/ingredients",
    f"/medicinal-product/ingredients/all?number={number}",
    f"/medicinal-product/all?number={number}",
    f"/medicinal-product/changelog?timestamp={timestamp}",
    # ---
    f"/organization?nplId={vet_npl_id}",
    "/organization/2058",
    # ---
    "/fass-document/20000225000063",
    "/fass-document/20000225000063?section=pregnancy-and-lactation",
    f"/fass-document/all?number={number}",
    f"/fass-document/changelog?timestamp={timestamp}",
    # ---
    "/fass-smpc/20000225000063",
    "/fass-smpc/20000225000063?section=contraindication",
    f"/fass-smpc/all?number={number}",
    f"/fass-smpc/changelog?timestamp={timestamp}",
    # ---
    "/fass-package-leaflet/10001226100304",
    f"/fass-package-leaflet/all?number={number}",
    f"/fass-package-leaflet/changelog?timestamp={timestamp}",
    # ---
    "/medicine-shortage?nplPackId=19630701100051",
    "/medicine-shortage/advice?nplPackId=20230309100048&referenceNumber=14796507-e2b4-4c85-98dd-9a68c0baa194",
    "/medicine-shortage/advice/ee83de64bd0532e94551c0818312a00d",
    "/medicine-shortage/url?adviceId=ee83de64bd0532e94551c0818312a00d",
    "/package?medicineShortageAdviceId=ee83de64bd0532e94551c0818312a00d",
    # ---
    "/online-pharmacy",
    "/pharmacy?cityId=412",
    "/custom/ehm/indication/20000225000063",
]

fass_organization_id = "2099"
substance_id = "IDE4POJRUCKPGVERT1"
npl_id = "20180613000025"
human_endpoints = [
    # --- ACCESS GROUP: UNAUTHORIZED
    "/alive",
    "/archived-medicinal-product/AP_00010080",
    f"/dhpc?nplId={npl_id}",
    # --- ACCESS GROUP: IVL
    "/fass-environmental-information-ready-for-review/231/ID6351709581637528",
    f"/fass-environmental-information-ready-for-review/changelog?timestamp={timestamp}",
    # --- ACCESS GROUP: SOLID-DOSAGE-FORM
    f"/solid-dosage-form/photo-identification?nplId={npl_id}",
    f"/solid-dosage-form/photo-identification/all?number={number}",
    f"/solid-dosage-form/photo-identification/changelog?timestamp={timestamp}",
    "/solid-dosage-form/photo-identification?solidDosageFormId=IDE4PONMUEPH5VERT1",
    "/solid-dosage-form/photo-identification/NBM2GW88",
    f"/solid-dosage-form/medication-management?nplId={npl_id}",
    "/solid-dosage-form/medication-management/IDE4PON6UECNNVERT1",
    f"/solid-dosage-form/medication-management/all?number={number}",
    f"/solid-dosage-form/medication-management/changelog?timestamp={timestamp}",
    # ---
    f"/medical-device?nplId={npl_id}",
    "/medical-device/ID11F1SYPGG3HAQCSR",
    f"/medical-device/all?number={number}",
    f"/medical-device/changelog?timestamp={timestamp}",
    # --- ACCESS GROUP: HUMAN / VETERINARY
    "/atc/N02BF02",
    "/atc/top-level",
    # ---
    "/dhpc/5587",
    f"/dhpc/all?number={number}",
    f"/dhpc/changelog?timestamp={timestamp}",
    # ---
    "/fass-educational-material/1702",
    f"/fass-educational-material/all?number={number}",
    f"/fass-educational-material/changelog?timestamp={timestamp}",
    # ---
    f"/fass-environmental-information?substanceId={substance_id}",
    f"/fass-environmental-information/{fass_organization_id}/{substance_id}",
    f"/fass-environmental-information/all?number={number}",
    f"/fass-environmental-information/changelog?timestamp={timestamp}",
    # ---
    f"/fass-document/{npl_id}",
    f"/fass-document/all?number={number}",
    f"/fass-document/changelog?timestamp={timestamp}",
    # ---
    f"/interchangeable-medicinal-products?nplId={npl_id}",
    # ---
    "/medicinal-product?atcGroup=A01",
    "/medicinal-product?atcCode=J01CE02",
    f"/medicinal-product?fassOrganizationId=915&substanceId={substance_id}",
    "/medicinal-product?fassOrganizationId=2336",
    "/medicinal-product?nplPackId=20080820100269",
    "/medicinal-product?medicineShortageAdviceId=8c1df1f0a768f074ae5e5812e31a5a02",
    f"/medicinal-product/{npl_id}",
    f"/medicinal-product/ingredients/all?number={number}",
    "/medicinal-product/search?query=Zevtera",
    f"/medicinal-product/all?number={number}",
    f"/medicinal-product/changelog?timestamp={timestamp}",
    # ---
    "/news/1166691_1718790410238",
    f"/news/all?number={number}",
    # ---
    "/organization/2058",
    f"/organization?nplId={npl_id}",
    f"/organization/all?number={number}",
    f"/organization/changelog?timestamp={timestamp}",
    # ---
    f"/package?nplId={npl_id}",
    f"/package?nplId={npl_id},20120809000026,19530228000028",
    "/package?nplPackId=19881001100108",
    "/package?nplPackId=19881001100108,10010101102494",
    "/package?itemNumber=009590",
    "/package?itemNumber=009590,406157",
    "/package?medicineShortageAdviceId=8c1df1f0a768f074ae5e5812e31a5a02",
    "/package?medicineShortageAdviceId=8c1df1f0a768f074ae5e5812e31a5a02,a8c5921ba2510268825ebb222a9faf67",
    f"/package/19881001100108",
    f"/package/all?number={number}",
    # ---
    "/fass-package-leaflet/20091110100098",
    f"/fass-package-leaflet/all?number={number}",
    f"/fass-package-leaflet/changelog?timestamp={timestamp}",
    # ---
    "/medicine-shortage?nplPackId=19630701100051",
    f"/medicine-shortage/advice?nplPackId=19960104100021&referenceNumber=e43c4d72-47af-49d1-886e-1f3c6952e7ea",
    "/medicine-shortage/advice/a8c5921ba2510268825ebb222a9faf67",
    "/medicine-shortage/url?adviceId=a8c5921ba2510268825ebb222a9faf67",
    # ---
    "/fass-safety-data-sheet/20060320000016",
    f"/fass-safety-data-sheet/all?number={number}",
    f"/fass-safety-data-sheet/changelog?timestamp={timestamp}",
    # ---
    f"/fass-smpc/{npl_id}",
    f"/fass-smpc/all?number={number}",
    f"/fass-smpc/changelog?timestamp={timestamp}",
    # ---
    f"/substance/all?number={number}",
    f"/substance/{substance_id}",
    f"/substance?nplId={npl_id}",
    f"/substance/changelog?timestamp={timestamp}",
    # ---
    f"/fass-supportive-material?nplId=20090211000016",
    "/fass-supportive-material/62",
    f"/fass-supportive-material/all?number={number}",
    f"/fass-supportive-material/changelog?timestamp={timestamp}",
    # ---
    "/glossary/all",
    # ---
    f"/vab/interchangeable?nplId={npl_id}",
    # ---
    "/fab/package/barcode/09006240025231",
    # ---
    "/vet/medicinal-product?atcCode=QP53AC04",
    f"/vet/species/all?number={number}",
    "/vet/species/atc/QP53",
    # --- ACCESS GROUP: FULL_ACCESS
    "/cities?countyCode=8",
    "/counties",
    f"/fab/organization/{fass_organization_id}/products",
    f"/fab/product/{npl_id}",
    "/online-pharmacy",
    "/pharmacy?cityId=412",
    "/pharmacy?countyCode=1",
    "/pharmacy?longitude=17.681710&latitude=59.858710",
    # "/pharmacy/stock/20091110100098", # POST
    f"/custom/ehm/indication/20180130000010",
    # --- ACCESS GROUP: UNKNOWN
    "/applicable-for?nplPackId=20080820100269",
    f"/applicable-for?nplId={npl_id}",
]
