package com.example.day1_ai_chat_nextgen.architecture

import com.tngtech.archunit.core.importer.ClassFileImporter
import com.tngtech.archunit.library.dependencies.SlicesRuleDefinition
import org.junit.Test

class ArchitectureTest {

    @Test
    fun `no package cycles`() {
        val imported = ClassFileImporter().importPackages("com.example.day1_ai_chat_nextgen")
        SlicesRuleDefinition.slices().matching("com.example.day1_ai_chat_nextgen.(*)..")
            .should().beFreeOfCycles()
            .check(imported)
    }

    @Test
    fun `layered architecture respected`() {
        val imported = ClassFileImporter().importPackages("com.example.day1_ai_chat_nextgen")
        val presentation = "com.example.day1_ai_chat_nextgen.presentation.."
        val domain = "com.example.day1_ai_chat_nextgen.domain.."
        val data = "com.example.day1_ai_chat_nextgen.data.."

        // 1) domain независим от presentation и data
        com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses().that()
            .resideInAPackage(domain)
            .should().dependOnClassesThat().resideInAnyPackage(presentation, data)
            .check(imported)

        // 2) presentation не зависит от data
        com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses().that()
            .resideInAPackage(presentation)
            .should().dependOnClassesThat().resideInAnyPackage(data)
            .check(imported)

        // 3) data не зависит от presentation
        com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses().that()
            .resideInAPackage(data)
            .should().dependOnClassesThat().resideInAnyPackage(presentation)
            .check(imported)
    }
}


