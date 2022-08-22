#define LCF_CSA0_SIZE 8k
#define LCF_USTACK0_SIZE 2k
#define LCF_ISTACK0_SIZE 1k

#define LCF_HEAP_SIZE  4k

#define LCF_CPU0 0

/*Un comment one of the below statements to enable CpuX DMI RAM to hold global variables*/
#define LCF_DEFAULT_HOST LCF_CPU0

#define LCF_DSPR0_START 0x70000000
#define LCF_DSPR0_SIZE  96k

#define LCF_CSA0_OFFSET     (LCF_DSPR0_SIZE - 1k - LCF_CSA0_SIZE)
#define LCF_ISTACK0_OFFSET  (LCF_CSA0_OFFSET - 256 - LCF_ISTACK0_SIZE)
#define LCF_USTACK0_OFFSET  (LCF_ISTACK0_OFFSET - 256 - LCF_USTACK0_SIZE)

#define LCF_HEAP0_OFFSET    (LCF_USTACK0_OFFSET - LCF_HEAP_SIZE)

#define FBLFLAGSOLD_OFFSET    0x0

#define EEP_DUMMYOLD_OFFSET    (FBLFLAGS_OFFSET + 16)

#define EEP_DUMMY_OFFSET	0x17E00

#define FBLFLAGS_OFFSET		0x17FE0

#define LCF_INTVEC0_START 0xA00FD000

#define LCF_TRAPVEC0_START 0xA0020100

#define LCF_STARTPTR_CPU0 0x80020000

#define LCF_STARTPTR_NC_CPU0 0xA0020000

#define INTTAB0             (LCF_INTVEC0_START)
#define TRAPTAB0            (LCF_TRAPVEC0_START)

#define RESET LCF_STARTPTR_NC_CPU0

#include "tc1v1_6_2.lsl"

// Specify a multi-core processor environment (mpe)

processor mpe
{
    derivative = tc33;
}

derivative tc33
{
    core tc0
    {
        architecture = TC1V1.6.2;
        space_id_offset = 100;            // add 100 to all space IDs in the architecture definition
        copytable_space = vtc:linear;     // use the copy table in the virtual core for 'bss' and initialized data sections
    }
        
    core vtc
    {
        architecture = TC1V1.6.2;
        import tc0;                     // add all address spaces of core tc0 to core vtc for linking and locating
    }
    
    bus sri
    {
        mau = 8;
        width = 32;
        
        // map shared addresses one-to-one to real cores and virtual cores
        map (dest=bus:tc0:fpi_bus, src_offset=0, dest_offset=0, size=0xc0000000);
        map (dest=bus:vtc:fpi_bus, src_offset=0, dest_offset=0, size=0xc0000000);
    }

    memory dsram0 // Data Scratch Pad Ram
    {
        mau = 8;
        size = 96k;
        type = ram;
        map (dest=bus:tc0:fpi_bus, dest_offset=0xd0000000, size=96k, priority=8);
        map (dest=bus:sri, dest_offset=0x70000000, size=96k);
    }
    
    memory psram0 // Program Scratch Pad Ram
    {
        mau = 8;
        size = 8k;
        type = ram;
        map (dest=bus:tc0:fpi_bus, dest_offset=0xc0000000, size=8k, priority=8);
        map (dest=bus:sri, dest_offset=0x70100000, size=8k);
    }
    
    memory pfls0
    {
        mau = 8;
        size = 896K;
        type = rom;
        map     cached (dest=bus:sri, dest_offset=0x80020000, reserved,          size=896K);
        map not_cached (dest=bus:sri, dest_offset=0xa0020000, size=896K);
    }
    
    memory dfls0
    {
        mau = 8;
        size = 128K;
        type = reserved nvram;
        map (dest=bus:sri, dest_offset=0xaf000000, size=128K);
    }
    
    memory ucb
    {
        mau = 8;
        size = 24k;
        type = rom;
        map (dest=bus:sri, dest_offset=0xaf400000, reserved, size=24k);
    }
    
    memory cpu0_dlmu
    {
        mau = 8;
        size = 8k;
        type = ram;
        map     cached (dest=bus:sri, dest_offset=0x90000000,           size=8k);
        map not_cached (dest=bus:sri, dest_offset=0xb0000000, reserved, size=8k);
    }

#if (__VERSION__ >= 6003)    
    section_setup :vtc:linear
    {
        heap "heap" (min_size = (1k), fixed, align = 8);
    }    
#endif
    
    section_setup :vtc:linear
    {
        start_address
        (
            symbol = "_START"
        );
    }
    
    section_setup :vtc:linear
    {
        stack "ustack_tc0" (min_size = 1k, fixed, align = 8);
        stack "istack_tc0" (min_size = 1k, fixed, align = 8);
    }
    
    /*Section setup for the copy table*/
    section_setup :vtc:linear
    {
        copytable
        (
            align = 4,
            dest = linear,
            table
            {
                symbol = "_lc_ub_table_tc0";
                space = :tc0:linear, :tc0:abs24, :tc0:abs18, :tc0:csa;
            }
        );
    }

    /*Sections located at absolute fixed address*/

    section_layout :vtc:linear
    {
        /*Fixed memory Allocations for stack memory and CSA*/
        group (ordered)
        {
            group ustack0(align = 8, run_addr = mem:dsram0[LCF_USTACK0_OFFSET])
            {
                stack "ustack_tc0" (size = LCF_USTACK0_SIZE);
            }
            "__USTACK0":= sizeof(group:ustack0) > 0  ? "_lc_ue_ustack_tc0" : 0;
            "__USTACK0_END"="_lc_gb_ustack0";
            
            group istack0(align = 8, run_addr = mem:dsram0[LCF_ISTACK0_OFFSET])
            {
                stack "istack_tc0" (size = LCF_ISTACK0_SIZE);
            }
            "__ISTACK0":= sizeof(group:istack0) > 0  ? "_lc_ue_istack_tc0" : 0;
            "__ISTACK0_END"="_lc_gb_istack0";
            
            group (align = 64, attributes=rw, run_addr=mem:dsram0[LCF_CSA0_OFFSET]) 
                reserved "csa_tc0" (size = LCF_CSA0_SIZE);
            "__CSA0":=        "_lc_ub_csa_tc0";
            "__CSA0_END":=    "_lc_ue_csa_tc0";
        }
		
		group (ordered)
		{
			group FblShareSection (ordered, contiguous, fill, align = 16, run_addr = mem:dsram0[FBLFLAGS_OFFSET])
			{
				section "FblShareSection_SEC" (blocksize = 2, attributes = rw)
				{
					select "[.]*.FblShareSection";
				}
			}
				group FblShareSection_PAD (align = 4)
			{
			reserved "FblShareSection_PAD" (size = 0);
			}
			"_FblShareSection_START" = "_lc_gb_FblShareSection";
			"_FblShareSection_END" = ("_lc_ge_FblShareSection" == 0) ? 0 : "_lc_ge_FblShareSection" - 1;
			"_FblShareSection_LIMIT" = "_lc_ge_FblShareSection";
		
			"_FblShareGroup_ALL_START" = "_FblShareSection_START";
			"_FblShareGroup_ALL_END" = "_FblShareSection_END";
			"_FblShareGroup_ALL_LIMIT" = "_FblShareSection_LIMIT";
		}
		group (ordered)
		{
			group EepDummySection (ordered, contiguous, fill, align = 16, run_addr = mem:dsram0[EEP_DUMMY_OFFSET])
			{
				section "EepDummySection_SEC" (blocksize = 2, attributes = rw)
				{
					select "[.]*.EepDummySection";
				}
			}
				group EepDummySection_PAD (align = 4)
			{
			reserved "EepDummySection_PAD" (size = 0);
			}
			"_EepDummySection_START" = "_lc_gb_EepDummySection";
			"_EepDummySection_END" = ("_lc_ge_EepDummySection" == 0) ? 0 : "_lc_ge_EepDummySection" - 1;
			"_EepDummySection_LIMIT" = "_lc_ge_EepDummySection";
		
			"_EepDummyGroup_ALL_START" = "_EepDummySection_START";
			"_EepDummyGroup_ALL_END" = "_EepDummySection_END";
			"_EepDummyGroup_ALL_LIMIT" = "_EepDummySection_LIMIT";
		}
		
		group (ordered)
		{
			group FblShareSectionOld (ordered, contiguous, fill, align = 16, run_addr = mem:dsram0[FBLFLAGSOLD_OFFSET])
			{
				section "FblShareSectionOld_SEC" (blocksize = 2, attributes = rw)
				{
					select "[.]*.FblShareSectionOld";
				}
			}
				group FblShareSectionOld_PAD (align = 4)
			{
			reserved "FblShareSectionOld_PAD" (size = 0);
			}
			"_FblShareSectionOld_START" = "_lc_gb_FblShareSectionOld";
			"_FblShareSectionOld_END" = ("_lc_ge_FblShareSectionOld" == 0) ? 0 : "_lc_ge_FblShareSectionOld" - 1;
			"_FblShareSectionOld_LIMIT" = "_lc_ge_FblShareSectionOld";
		
			"_FblShareGroupOld_ALL_START" = "_FblShareSectionOld_START";
			"_FblShareGroupOld_ALL_END" = "_FblShareSectionOld_END";
			"_FblShareGroupOld_ALL_LIMIT" = "_FblShareSectionOld_LIMIT";
		}
		group (ordered)
		{
			group EepDummySectionOld (ordered, contiguous, fill, align = 16, run_addr = mem:dsram0[EEP_DUMMYOLD_OFFSET])
			{
				section "EepDummySectionOld_SEC" (blocksize = 2, attributes = rw)
				{
					select "[.]*.EepDummySectionOld";
				}
			}
				group EepDummySectionOld_PAD (align = 4)
			{
			reserved "EepDummySectionOld_PAD" (size = 0);
			}
			"_EepDummySectionOld_START" = "_lc_gb_EepDummySectionOld";
			"_EepDummySectionOld_END" = ("_lc_ge_EepDummySectionOld" == 0) ? 0 : "_lc_ge_EepDummySectionOld" - 1;
			"_EepDummySectionOld_LIMIT" = "_lc_ge_EepDummySectionOld";
		
			"_EepDummyGroupOld_ALL_START" = "_EepDummySectionOld_START";
			"_EepDummyGroupOld_ALL_END" = "_EepDummySectionOld_END";
			"_EepDummyGroupOld_ALL_LIMIT" = "_EepDummySectionOld_LIMIT";
		}
        
        /*Fixed memory Allocations for _START*/
        group (ordered)
        {
            group  reset (run_addr=RESET)
            {
                section "reset" ( size = 0x20, fill = 0x0800, attributes = r )
                {
                    select ".text.start";
                }
            }
            group  interface_const (run_addr=mem:pfls0/not_cached[0x0020])
            {
                select "*.interface_const";
            }
            "__IF_CONST" := addressof(group:interface_const);
            "__START0" := LCF_STARTPTR_NC_CPU0;
        }
        
        /*Fixed memory Allocations for Trap Vector Table*/
        group (ordered)
        {
            group trapvec_tc0 (align = 8, run_addr=LCF_TRAPVEC0_START)
            {
                section "trapvec_tc0" (size=0x100, attributes=rx, fill=0)
                {
                    select "([.]text.OS_EXCVEC_CORE0_CODE)";
                }
            }
            "__TRAPTAB_CPU0" := TRAPTAB0;
        }
        
        /*Fixed memory Allocations for Start up code*/
        group (ordered)
        {
            group start_tc0 (run_addr=LCF_STARTPTR_NC_CPU0)
            {
                select "(.text.start_cpu0*)";
            }
            "__ENABLE_INDIVIDUAL_C_INIT_CPU0" := 0; /* Not used */
        }
        
        /*Fixed memory Allocations for Interrupt Vector Table*/
        group (ordered)
        {
            group int_tab_tc0 (run_addr=LCF_INTVEC0_START)
            {
				select "([.]text.OS_INTVEC_CORE0_CODE*)";
            }
            "_lc_u_int_tab" = (LCF_INTVEC0_START);
            "__INTTAB_CPU0" = (LCF_INTVEC0_START);
        }
        
        /*Fixed memory Allocations for BMHD*/
        group (ordered)
        {
            group  bmh_0_orig (run_addr=mem:ucb[0x0000])
            {
                select ".rodata.bmhd_0_orig";
            }
            group  bmh_1_orig (run_addr=mem:ucb[0x0200])
            {
                select ".rodata.bmhd_1_orig";
            }
            group  bmh_2_orig (run_addr=mem:ucb[0x0400])
            {
                select ".rodata.bmhd_2_orig";
            }
            group  bmh_3_orig (run_addr=mem:ucb[0x0600])
            {
                select ".rodata.bmhd_3_orig";
            }
            group  bmh_blank (run_addr=mem:ucb[0x0800])
            {
            }
            group  bmh_0_copy (run_addr=mem:ucb[0x1000])
            {
                select ".rodata.bmhd_0_copy";
            }
            group  bmh_1_copy (run_addr=mem:ucb[0x1200])
            {
                select ".rodata.bmhd_1_copy";
            }
            group  bmh_2_copy (run_addr=mem:ucb[0x1400])
            {
                select ".rodata.bmhd_2_copy";
            }
            group  bmh_3_copy (run_addr=mem:ucb[0x1600])
            {
                select ".rodata.bmhd_3_copy";
            }
        }
    }
        
    /*Near Abbsolute Addressable Data Sections*/
    section_layout :vtc:abs18
    {
        /*Near Absolute Data, selectable with patterns and user defined sections*/
        group
        {            
            group (ordered, contiguous, align = 4, attributes=rw, run_addr = mem:dsram0)
            {
                select "(.zdata.zdata_cpu0|.zdata.zdata_cpu0.*)";
                select "(.zbss.zbss_cpu0|.zbss.zbss_cpu0.*)";
            }
            
            group (ordered, attributes=rw, run_addr = mem:cpu0_dlmu)
            {
                select "(.zdata.zlmudata|.zdata.zlmudata.*)";
                select "(.zbss.zlmubss|.zbss.zlmubss.*)";
            } 
        }

        /*Near Absolute Data, selectable by toolchain*/
#        if LCF_DEFAULT_HOST == LCF_CPU0
        group (ordered, contiguous, align = 4, attributes=rw, run_addr = mem:dsram0)
#        endif
        {
            group zdata_mcal(attributes=rw)
            {
                select ".zdata.dsprInit.cpu0.32bit";
                select ".zdata.dsprInit.cpu0.16bit";
                select ".zdata.dsprInit.cpu0.8bit";
            }
            
            group zdata_powerOn(attributes=rw)
            {
                select ".zdata.dsprPowerOnInit.cpu0.32bit";
                select ".zdata.dsprPowerOnInit.cpu0.16bit";
                select ".zdata.dsprPowerOnInit.cpu0.8bit";
            }
            
            group zbss_mcal(attributes=rw)
            {
                select ".zbss.dsprClearOnInit.cpu0.32bit";
                select ".zbss.dsprClearOnInit.cpu0.16bit";
                select ".zbss.dsprClearOnInit.cpu0.8bit";
            }
            
            group zbss_noClear(attributes=rw)
            {
                select ".zbss.dsprNoInit.cpu0.32bit";
                select ".zbss.dsprNoInit.cpu0.16bit";
                select ".zbss.dsprNoInit.cpu0.8bit";
            }
            
            group zbss_powerOn(attributes=rw)
            {
                select ".zbss.dsprPowerOnClear.cpu0.32bit";
                select ".zbss.dsprPowerOnClear.cpu0.16bit";
                select ".zbss.dsprPowerOnClear.cpu0.8bit";
            }
            
            group zdata(attributes=rw)
            {
                select "(.zdata|.zdata.*)";
                select "(.zbss|.zbss.*)";
            }
        }
        
        /*Near Absolute Const, selectable with patterns and user defined sections*/
        group
        {
            group (ordered, align = 4, contiguous, run_addr=mem:pfls0/not_cached)
            {
                select ".zrodata.Ifx_Ssw_Tc0.*";
                select ".zrodata.Cpu0_Main.*";
                
                /*Near Absolute Const, selectable by toolchain*/
                select ".zrodata.const.cpu0.32bit";
                select ".zrodata.const.cpu0.16bit";
                select ".zrodata.const.cpu0.8bit";
                select ".zrodata.config.cpu0.32bit";
                select ".zrodata.config.cpu0.16bit";
                select ".zrodata.config.cpu0.8bit";
                select "(.zrodata|.zrodata.*)";
            }
        }
    }
        
    /*Relative A0/A1/A8/A9 Addressable Sections*/
    section_layout :vtc:linear
    {
        /*Relative A0 Addressable Data, selectable by toolchain*/
#        if LCF_DEFAULT_HOST == LCF_CPU0
        group a0 (ordered, contiguous, align = 4, attributes=rw, run_addr = mem:dsram0)
#        endif
        {
            select "(.data_a0.sdata|.data_a0.sdata.*)";
            select "(.bss_a0.sbss|.bss_a0.sbss.*)";
        }
        "_SMALL_DATA_" := sizeof(group:a0) > 0 ? addressof(group:a0) : addressof(group:a0) & 0xF0000000 + 32k;
        "__A0_MEM" = "_SMALL_DATA_";
        
        /*Relative A1 Addressable Const, selectable by toolchain*/
        /*Small constant sections, No option given for CPU specific user sections to make generated code portable across Cpus*/
#        if LCF_DEFAULT_HOST == LCF_CPU0
        group  a1 (ordered, align = 4, run_addr=mem:pfls0)
#        endif
        {
            select "(.rodata_a1.srodata|.rodata_a1.srodata.*)";
            select "(.ldata|.ldata.*)";
        }
        "_LITERAL_DATA_" := sizeof(group:a1) > 0 ? addressof(group:a1) : addressof(group:a1) & 0xF0000000 + 32k;
        "__A1_MEM" = "_LITERAL_DATA_";
        
        /*Relative A9 Addressable Data, selectable with patterns and user defined sections*/
        group a9 (ordered, align = 4, run_addr=mem:cpu0_dlmu)
        {
            select "(.data_a9.a9sdata|.data_a9.a9sdata.*)";
            select "(.bss_a9.a9sbss|.bss_a9.a9sbss.*)";
        }
        "_A9_DATA_" := sizeof(group:a9) > 0 ? addressof(group:a9) : addressof(group:a9) & 0xF0000000 + 32k;
        "__A9_MEM" = "_A9_DATA_";

        /*Relative A8 Addressable Const, selectable with patterns and user defined sections*/
#        if LCF_DEFAULT_HOST == LCF_CPU0
        group  a8 (ordered, align = 4, run_addr=mem:pfls0)
#        endif
        {
            select "(.rodata_a8.a8srodata|.rodata_a8.a8srodata.*)";
        }
        "_A8_DATA_" := sizeof(group:a8) > 0 ? addressof(group:a8) : addressof(group:a8) & 0xF0000000 + 32k;
        "__A8_MEM" = "_A8_DATA_";
    }
        
    /*Far Data / Far Const Sections, selectable with patterns and user defined sections*/
    section_layout :vtc:linear
    {
        group OS_CODE_GROUP (ordered, run_addr = mem:pfls0/not_cached)
		{
			group OS_CODE (ordered, contiguous, fill)
			{
			section "OS_CODE_SEC" (fill, blocksize = 2, attributes = rx)
			{
				select "[.]text.OS_CODE";
				select "[.]text.OS_OS_COREINITHOOK_CODE";
			}
			}
			group OS_CODE_PAD (align = 1)
			{
			reserved "OS_CODE_PAD" (size = 16);
			}
			"_OS_CODE_START" = "_lc_gb_OS_CODE";
			"_OS_CODE_END" = ("_lc_gb_OS_CODE_PAD" == 0) ? 0 : "_lc_gb_OS_CODE_PAD" - 1;
			"_OS_CODE_LIMIT" = "_lc_gb_OS_CODE_PAD";
		
			"_OS_CODE_ALL_START" = "_OS_CODE_START";
			"_OS_CODE_ALL_END" = "_OS_CODE_END";
			"_OS_CODE_ALL_LIMIT" = "_OS_CODE_LIMIT";
		}
		
		/*Far Data Sections, selectable with patterns and user defined sections*/
        group
        {
            /*DSRAM sections*/
            group
            {
                group (ordered, attributes=rw, run_addr=mem:dsram0)
                {
                    select ".data.Ifx_Ssw_Tc0.*";
                    select ".data.Cpu0_Main.*";
                    select "(.data.data_cpu0|.data.data_cpu0.*)";
                     /* Initialized Data */
                    select "*InitData.Cpu0.8bit";
                    select "*InitData.Cpu0.16bit";
                    select "*InitData.Cpu0.32bit";
                    select "*InitData.Cpu0.256bit";
                    select "*InitData.Cpu0.Unspecified";
                    select "*InitData.Fast.Cpu0.8bit";
                    select "*InitData.Fast.Cpu0.16bit";
                    select "*InitData.Fast.Cpu0.32bit";
                    select "*InitData.Fast.Cpu0.256bit";
                    select "*InitData.Fast.Cpu0.Unspecified";
                    select ".bss.Ifx_Ssw_Tc0.*";
                    select ".bss.Cpu0_Main.*";
                    select "(.bss.bss_cpu0|.bss.bss_cpu0.*)";
                   /* UnInitialized Data */
                     select "*ClearedData.Cpu0.8bit";
                     select "*ClearedData.Cpu0.16bit";
                     select "*ClearedData.Cpu0.32bit";
                     select "*ClearedData.Cpu0.256bit";
                     select "*ClearedData.Cpu0.Unspecified";
                     select "*ClearedData.Fast.Cpu0.8bit";
                     select "*ClearedData.Fast.Cpu0.16bit";
                     select "*ClearedData.Fast.Cpu0.32bit";
                     select "*ClearedData.Fast.Cpu0.256bit";
                     select "*ClearedData.Fast.Cpu0.Unspecified";
                }
            }

            /*LMU Data sections*/
            group
            {
                group (ordered, attributes=rw, run_addr = mem:cpu0_dlmu)
                {
                    select "(.data.lmudata_cpu0|.data.lmudata_cpu0.*|.data.*.lmudata_cpu0)";
                    select "(.bss.lmubss_cpu0|.bss.lmubss_cpu0.*|.bss.*.lmubss_cpu0)";
                    select "(.data.lmudata|.data.lmudata.*)";
                    select "(.bss.lmubss|.bss.lmubss.*)";
                }
          group (ordered, attributes=rw, run_addr = mem:cpu0_dlmu/not_cached)
          {
            /* Initialized Data */
            select "*InitData.LmuNC.8bit";
            select "*InitData.LmuNC.16bit";
            select "*InitData.LmuNC.32bit";
            select "*InitData.LmuNC.256bit";
            select "*InitData.LmuNC.Unspecified";
            select "*InitData.Fast.LmuNC.8bit";
            select "*InitData.Fast.LmuNC.16bit";
            select "*InitData.Fast.LmuNC.32bit";
            select "*InitData.Fast.LmuNC.256bit";
            select "*InitData.Fast.LmuNC.Unspecified";      
            /* UnInitialized Data */
            select "*ClearedData.LmuNC.8bit";
            select "*ClearedData.LmuNC.16bit";
            select "*ClearedData.LmuNC.32bit";
            select "*ClearedData.LmuNC.256bit";
            select "*ClearedData.LmuNC.Unspecified";
            select "*ClearedData.Fast.LmuNC.8bit";
            select "*ClearedData.Fast.LmuNC.16bit";
            select "*ClearedData.Fast.LmuNC.32bit";
            select "*ClearedData.Fast.LmuNC.256bit";
            select "*ClearedData.Fast.LmuNC.Unspecified";     
          }
            }
        }
        
        /*Far Data Sections, selectable by toolchain*/
#        if LCF_DEFAULT_HOST == LCF_CPU0
        group (ordered, contiguous, align = 4, attributes=rw, run_addr = mem:dsram0)
#        endif
        {
            group data_mcal(attributes=rw)
            {
                select ".data.farDsprInit.cpu0.32bit";
                select ".data.farDsprInit.cpu0.16bit";
                select ".data.farDsprInit.cpu0.8bit";
            }
            
            group bss_mcal(attributes=rw)
            {
                select ".bss.farDsprClearOnInit.cpu0.32bit";
                select ".bss.farDsprClearOnInit.cpu0.16bit";
                select ".bss.farDsprClearOnInit.cpu0.8bit";
            }
            
            group bss_noInit(attributes=rw)
            {
                select ".bss.farDsprNoInit.cpu0.32bit";
                select ".bss.farDsprNoInit.cpu0.16bit";
                select ".bss.farDsprNoInit.cpu0.8bit";                
            }
            
            group data(attributes=rw)
            {
                select "(.data|.data.*)";
                select "(.bss|.bss.*)";
            }
        }
        
        /*Heap allocation*/
#        if LCF_DEFAULT_HOST == LCF_CPU0
        group (ordered, align = 4, run_addr = mem:dsram0[LCF_HEAP0_OFFSET])
#        endif
        {
            heap "heap" (size = LCF_HEAP_SIZE);
        }
        
        /*Far Const Sections, selectable with patterns and user defined sections*/
        group
        {
            group (ordered, align = 4, run_addr=mem:pfls0/not_cached)
            {
                select ".rodata.Ifx_Ssw_Tc0.*";
                select ".rodata.Cpu0_Main.*";
          /* Const Data */        
          select "*Const.Cpu0.8bit";
          select "*Const.Cpu0.16bit";
          select "*Const.Cpu0.32bit";
          select "*Const.Cpu0.Unspecified";
          select "*Const.Cpu0.256bit";
          /* Config Data */      
          select "*Config.Cpu0.8bit";
          select "*Config.Cpu0.16bit";
          select "*Config.Cpu0.32bit";
          select "*Config.Cpu0.Unspecified";
          select "*Config.Cpu0.256bit";
                select "(.rodata.rodata_cpu0|.rodata.rodata_cpu0.*)";
            }
        }

        /*Far Const Sections, selectable by toolchain*/
#        if LCF_DEFAULT_HOST == LCF_CPU0
        group (ordered, align = 4, run_addr=mem:pfls0/not_cached)
#        endif
        {
            select ".rodata.farConst.cpu0.32bit";
            select ".rodata.farConst.cpu0.16bit";
            select ".rodata.farConst.cpu0.8bit";
            select "(.rodata|.rodata.*)";
        }
    }
    section_layout :vtc:linear
    {
        group FLSLOADER_CODE (ordered, attributes=rwx, copy, run_addr=mem:psram0)
        {
           select ".text.FLSLOADERRAMCODE*";
        }
    }
    
    /* PSRAM Code selections*/
    section_layout :vtc:linear
    {
        /*Code Sections, selectable with patterns and user defined sections*/
        group
        {
            /*Program Scratchpad Sections*/
            group
            {
                group code_psram0 (ordered, attributes=rwx, copy, run_addr=mem:psram0)
                {
                    select "(.text.cpu0_psram|.text.cpu0_psram.*)";
                    select "(.text.psram_text_cpu0|.text.psram_text_cpu0.*)";
                }
            }
        }
    }
    
    /* FLS Code selections*/
    section_layout :vtc:linear
    {
        /*Code Sections, selectable with patterns and user defined sections*/
        group
        {    
            /*Cpu specific PFLASH Sections*/
            group
            {
                group (ordered, align = 4, run_addr=mem:pfls0/not_cached)
                {
                    select ".text.Ifx_Ssw_Tc0.*";
                    select ".text.Cpu0_Main.*";
                    select ".text.CompilerTasking.Ifx_C_Init";
                    select "(.text.text_cpu0|.text.text_cpu0.*)";
                    select "*Code.Cpu0";
                    select "*Code.Fast.Cpu0";
                }
            }
        }
        
        /*Code Sections, selectable by toolchain*/
#        if LCF_DEFAULT_HOST == LCF_CPU0
        group (ordered, run_addr=mem:pfls0/not_cached)
#        endif
        {
            select ".text.fast.pfls.cpu0";
            select ".text.slow.pfls.cpu0";
            select ".text.5ms.pfls.cpu0";
            select ".text.10ms.pfls.cpu0";
            select ".text.callout.pfls.cpu0";
            select "(.text|.text.*)";
        }
    }

}
