
ENTRY_ANNOTATIONS = """rcsb_id
entry {
  id
}
database_2 {
  database_id
  pdbx_database_accession
}
rcsb_comp_model_provenance {
  source_url
  entry_id
  source_db
}
rcsb_associated_holdings {
  rcsb_repository_holdings_current_entry_container_identifiers {
    assembly_ids
  }
  rcsb_repository_holdings_current {
    repository_content_types
  }
}
rcsb_external_references {
  id
  type
  link
}
rcsb_entry_container_identifiers {
  emdb_ids
}
pdbx_database_status {
  pdb_format_compatible
}
struct {
  title
}
rcsb_entry_info {
  structure_determination_methodology
}
polymer_entities {
  entity_poly {
    rcsb_entity_polymer_type
    pdbx_seq_one_letter_code_can
  }
  rcsb_polymer_entity_container_identifiers {
    entry_id
    entity_id
    asym_ids
    auth_asym_ids
  }
  rcsb_polymer_entity_feature {
    type
    feature_id
    name
    provenance_source
    assignment_version
    feature_positions {
      end_seq_id
      beg_seq_id
    }
    additional_properties {
      name
      values
    }
    description
  }
  rcsb_id
  chem_comp_nstd_monomers {
    rcsb_id
    chem_comp {
      mon_nstd_parent_comp_id
    }
    rcsb_chem_comp_annotation {
      type
      annotation_id
      name
    }
    rcsb_chem_comp_related {
      resource_accession_code
      resource_name
    }
  }
  pfams {
    rcsb_id
    rcsb_pfam_accession
    rcsb_pfam_identifier
    rcsb_pfam_comment
    rcsb_pfam_description
    rcsb_pfam_seed_source
  }
  uniprots {
    rcsb_id
    rcsb_uniprot_annotation {
      annotation_id
      type
      name
      description
      assignment_version
      annotation_lineage {
        id
        name
        depth
      }
      additional_properties {
        name
        values
      }
    }
  }
  rcsb_polymer_entity_annotation {
    annotation_id
    type
    name
    description
    assignment_version
    additional_properties {
      name
      values
    }
    annotation_lineage {
      id
      name
      depth
    }
  }
  rcsb_polymer_entity {
    pdbx_description
    rcsb_enzyme_class_combined {
      ec
      provenance_source
    }
  }
  rcsb_entity_source_organism {
    ncbi_taxonomy_id
    common_name
    scientific_name
    ncbi_scientific_name
  }
  polymer_entity_instances {
    rcsb_polymer_entity_instance_container_identifiers {
      asym_id
      entity_id
      auth_asym_id
      auth_to_entity_poly_seq_mapping
    }
    rcsb_polymer_instance_feature {
      ordinal
      type
      feature_id
      name
      provenance_source
      assignment_version
      feature_positions {
        end_seq_id
        beg_seq_id
      }
      reference_scheme
      additional_properties {
        name
        values
      }
    }
    rcsb_polymer_instance_annotation {
      annotation_id
      type
      assignment_version
      name
      description
      provenance_source
      annotation_lineage {
        id
        name
        depth
      }
    }
    rcsb_polymer_instance_feature_summary {
      coverage
      type
      count
    }
  }
}
exptl {
  method
}
nonpolymer_entities {
  nonpolymer_comp {
    chem_comp {
      id
    }
  }
  nonpolymer_entity_instances {
    rcsb_nonpolymer_instance_validation_score {
      ranking_model_fit
      ranking_model_geometry
      is_subject_of_investigation
    }
  }
}
assemblies {
  rcsb_assembly_feature {
    assignment_version
    description
    feature_id
    name
    provenance_source
    type
    feature_positions {
      asym_id
      beg_seq_id
      struct_oper_list
    }
    additional_properties {
      name
      values
    }
  }
}"""

ENTRY_EXP_INFO="""rcsb_id
entry {
  id
}
database_2 {
  database_id
  pdbx_database_accession
}
struct {
  title
}
exptl {
  method
}
rcsb_ihm_dataset_list {
  name
  type
  count
}
rcsb_ihm_dataset_source_db_reference {
  db_name
  accession_code
}
rcsb_entry_info {
  structure_determination_methodology
}
ihm_external_reference_info {
  reference
  associated_url
  reference_provider
}
pdbx_soln_scatter {
  id 
  type
  source_type
  source_class
  source_beamline
  source_beamline_instrument
  detector_type
  detector_specific
  temperature
  sample_pH
  num_time_frames
  concentration_range
  buffer_name
  data_reduction_software_list
  mean_guiner_radius
  mean_guiner_radius_esd
  min_mean_cross_sectional_radii_gyration
  min_mean_cross_sectional_radii_gyration_esd
  max_mean_cross_sectional_radii_gyration
  max_mean_cross_sectional_radii_gyration_esd
  protein_length
}
pdbx_soln_scatter_model {
  method
  software_list
  software_author_list
  entry_fitting_list
  num_conformers_calculated
  num_conformers_submitted
  conformer_selection_criteria
  representative_conformer
  details
}
exptl_crystal_grow {
  crystal_id
  method
  pH
  temp
  pdbx_details
}
exptl_crystal {
  density_Matthews
  density_percent_sol
}
cell {
  length_a
  length_b
  length_c
  angle_alpha
  angle_beta
  angle_gamma
}
symmetry {
   space_group_name_H_M
}
diffrn {
  id
  crystal_id
  ambient_temp
  pdbx_serial_crystal_experiment
}
diffrn_detector {
  diffrn_id
  detector
  details
  pdbx_collection_date
  type
}
diffrn_radiation {
  diffrn_id
  pdbx_monochromatic_or_laue_m_l
  pdbx_diffrn_protocol
  pdbx_scattering_type
}
diffrn_source {
  diffrn_id
  source
  type
  pdbx_wavelength_list
  pdbx_synchrotron_site
  pdbx_synchrotron_beamline
}
 pdbx_serial_crystallography_sample_delivery {
  diffrn_id
  description
  method
}
pdbx_serial_crystallography_sample_delivery_fixed_target {
  diffrn_id
  sample_holding
  support_base
  motion_control
  description
  details
  sample_solvent
}
pdbx_serial_crystallography_sample_delivery_injection {
  diffrn_id
  flow_rate
  jet_diameter
  power_by
  injector_nozzle
  description
  filter_size
  carrier_solvent
}
pdbx_serial_crystallography_measurement {
  diffrn_id
  pulse_duration
  xfel_pulse_repetition_rate
  focal_spot_size
  pulse_photon_energy
  photons_per_pulse
}
pdbx_serial_crystallography_data_reduction {
  diffrn_id
  frames_indexed
  crystal_hits
  frames_total
  lattices_merged
}
reflns {
  pdbx_diffrn_id
  d_resolution_high
  d_resolution_low
  percent_possible_obs
  pdbx_Rmerge_I_obs
  pdbx_Rsym_value
  pdbx_Rpim_I_all
  pdbx_Rrim_I_all
  pdbx_CC_half
  pdbx_R_split
  pdbx_netI_over_sigmaI
  pdbx_redundancy
  number_obs
  number_all
  observed_criterion_sigma_F
  observed_criterion_sigma_I
  B_iso_Wilson_estimate
}
reflns_shell {
  pdbx_diffrn_id
  d_res_high
  d_res_low
  percent_possible_all
  percent_possible_obs
  Rmerge_I_obs
  pdbx_Rsym_value
  pdbx_Rrim_I_all
  pdbx_Rpim_I_all
  pdbx_CC_half
  pdbx_R_split
  meanI_over_sigI_obs
  pdbx_redundancy
  number_unique_all
}
refine {
  pdbx_refine_id
  ls_d_res_high
  ls_d_res_low
  pdbx_method_to_determine_struct
  pdbx_ls_sigma_I
  pdbx_ls_sigma_F
  ls_number_reflns_all
  ls_number_reflns_obs
  ls_number_reflns_R_free
  ls_percent_reflns_obs
  ls_R_factor_all
  ls_R_factor_obs
  ls_R_factor_R_work
  ls_R_factor_R_free
  pdbx_R_Free_selection_details
  B_iso_mean
  pdbx_ls_cross_valid_method
  pdbx_starting_model
  aniso_B_1_1
  aniso_B_1_2
  aniso_B_1_3
  aniso_B_2_2
  aniso_B_2_3
  aniso_B_3_3 
}
pdbx_vrpt_summary_diffraction {
  DCC_R
  DCC_Rfree
}
refine_ls_restr {
  type
  dev_ideal
}
refine_analyze {
  number_disordered_residues
  occupancy_sum_hydrogen
  occupancy_sum_non_hydrogen
}
refine_hist {
  pdbx_number_atoms_protein
  pdbx_number_atoms_nucleic_acid
  number_atoms_solvent
  pdbx_number_atoms_ligand
}
software {
  classification
  name
}
pdbx_nmr_sample_details {
  solution_id
  contents
  solvent_system
}
pdbx_nmr_exptl_sample_conditions {
  conditions_id
  ionic_strength
  ionic_strength_units
  pH
  pressure
  pressure_units
  temperature
}
pdbx_nmr_exptl {    
  conditions_id
  experiment_id
  sample_state
  solution_id
  spectrometer_id
  type
}
pdbx_nmr_spectrometer {
  spectrometer_id
  manufacturer
  model
  field_strength
}
pdbx_nmr_representative {
  conformer_id
  selection_criteria
}
pdbx_nmr_refine {
  method
  details
  software_ordinal
}
pdbx_nmr_ensemble {
  conformers_calculated_total_number
  conformers_submitted_total_number
  conformer_selection_criteria
}
pdbx_nmr_details {
  text
}
pdbx_nmr_software {
  ordinal
  classification
  version
  name
  authors
}
em_experiment {
  aggregation_state
  reconstruction_method
}
em_entity_assembly {
  name
}
em_vitrification {
  instrument
  cryogen_name
  details
}
em_staining {
  type
  material
  details
}
em_embedding {
  material
  details
}
em_image_recording {
  film_or_detector_model
  avg_electron_dose_per_image
}
em_imaging {
  id   
  date
  temperature
  microscope_model
  nominal_defocus_min
  nominal_defocus_max
  tilt_angle_min
  tilt_angle_max
  nominal_cs
  mode
  specimen_holder_model
  nominal_magnification
  calibrated_magnification
  electron_source
  accelerating_voltage
  details
}
em_software {
  category  
  name
  version
}
em_3d_reconstruction {
  num_particles
  resolution
  details
  resolution_method
  refinement_type
  symmetry_type
}
em_single_particle_entity {
  point_symmetry
}
em_helical_entity {
  axial_symmetry
  axial_rise_per_subunit
  angular_rotation_per_subunit
}
em_2d_crystal_entity {
  space_group_name_H_M
  length_a
  length_b
  angle_gamma
}
em_3d_crystal_entity {
space_group_name
  length_a
  length_b
  length_c
  angle_alpha
  angle_beta
  angle_gamma
}
em_3d_fitting {
  id
  ref_space
  ref_protocol
  target_criteria
  overall_b_value
  method
  details
}
em_3d_fitting_list {
  _3d_fitting_id
  pdb_chain_id 
  pdb_entry_id
}
em_ctf_correction {
  em_image_processing_id
  type
  details
}
em_particle_selection {
  image_processing_id
  num_particles_selected
  details
}
pdbx_initial_refinement_model {
  accession_code
  type
  source_name
  details
}"""