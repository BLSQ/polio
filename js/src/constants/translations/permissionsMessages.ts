/* eslint-disable max-len */
import { defineMessages } from 'react-intl';
import { PermissionsMessages } from 'Iaso/domains/users/permissionsMessages';

export const PERMISSIONS_GROUPS_MESSAGES: PermissionsMessages = defineMessages({
    polio: {
        id: 'iaso.permissions.group.polio',
        defaultMessage: 'Polio campaigns management',
    },
});

export const PERMISSIONS_MESSAGES: PermissionsMessages = defineMessages({
    iaso_polio: {
        id: 'iaso.permissions.polio',
        defaultMessage: 'Polio campaigns management - User',
    },
    iaso_polio_tooltip: {
        id: 'iaso.permissions.tooltip.polio',
        defaultMessage:
            'Manage Polio campaigns data entry, grouped campaigns, SIA calendar, LQAS/IM results',
    },
    iaso_polio_budget: {
        id: 'iaso.permissions.polio_budget',
        defaultMessage: 'Polio budget - User',
    },
    iaso_polio_budget_tooltip: {
        id: 'iaso.permissions.tooltip.polio_budget',
        defaultMessage:
            'View budget approval process and take action as defined by your role in the process',
    },
    iaso_polio_budget_admin: {
        id: 'iaso.permissions.polio_budget_admin',
        defaultMessage: 'Polio budget - Admin',
    },
    iaso_polio_budget_admin_tooltip: {
        id: 'iaso.permissions.tooltip.polio_budget_admin',
        defaultMessage:
            'View budget approval process and take action as defined by your role in the process. Extra admin powers: Override any step in the process if needed.',
    },
    iaso_polio_config: {
        id: 'iaso.permissions.polio_config',
        defaultMessage: 'Polio campaigns management - Admin',
    },
    iaso_polio_config_tooltip: {
        id: 'iaso.permissions.tooltip.polio_config',
        defaultMessage:
            'Manage Polio campaigns data entry, grouped campaigns, SIA calendar, LQAS/IM results. Extra admin powers: test campaigns, debug information LQAS/IM, Country configuration page (weekly email alerts recipients, language per country and budget teams management)',
    },
    iaso_polio_vaccine_authorizations_admin: {
        id: 'iaso.permissions.polio_vaccine_authorizations_admin',
        defaultMessage: 'Polio Vaccine Authorizations: Admin',
    },
    iaso_polio_vaccine_authorizations_read_only: {
        id: 'iaso.permissions.polio_vaccine_authorizations_read_only',
        defaultMessage: 'Polio Vaccine Authorizations: Read Only',
    },
    iaso_polio_vaccine_authorizations_admin_tooltip: {
        id: 'iaso.permissions.tooltip.polio_vaccine_authorizations_admin',
        defaultMessage: 'Manage polio vaccine authorizations - Read and Write',
    },
    iaso_polio_vaccine_authorizations_read_only_tooltip: {
        id: 'iaso.permissions.tooltip.polio_vaccine_authorizations_read_only',
        defaultMessage: 'Manage polio vaccine authorizations - Read Only',
    },
    iaso_polio_vaccine_supply_chain_write: {
        id: 'iaso.permissions.iaso_polio_vaccine_supply_chain_write',
        defaultMessage: 'Polio vaccine supply chain - Write',
    },
    iaso_polio_vaccine_supply_chain_read: {
        id: 'iaso.permissions.iaso_polio_vaccine_supply_chain_read',
        defaultMessage: 'Polio vaccine supply chain - Read',
    },
    iaso_polio_vaccine_stock_earmarks_nonadmin: {
        id: 'iaso.permissions.iaso_polio_vaccine_stock_earmarks_nonadmin',
        defaultMessage: 'Polio vaccine stock earmarks - Non-admin',
    },
    iaso_polio_vaccine_stock_earmarks_nonadmin_tooltip: {
        id: 'iaso.permissions.iaso_polio_vaccine_stock_earmarks_nonadmin_tooltip',
        defaultMessage:
            'See summary of vaccine stock earmarks, by country and vaccine',
    },
    iaso_polio_vaccine_stock_earmarks_admin: {
        id: 'iaso.permissions.iaso_polio_vaccine_stock_earmarks_admin',
        defaultMessage: 'Polio vaccine stock earmarks - Admin',
    },
    iaso_polio_vaccine_stock_earmarks_admin_tooltip: {
        id: 'iaso.permissions.iaso_polio_vaccine_stock_earmarks_admin_tooltip',
        defaultMessage: 'Edit and add vaccine stock earmarks data',
    },
    iaso_polio_vaccine_supply_chain_read_tooltip: {
        id: 'iaso.permissions.iaso_polio_vaccine_supply_chain_read_tooltip',
        defaultMessage:
            'See summary of vaccine supply chain, by country and vaccine',
    },
    iaso_polio_vaccine_supply_chain_write_tooltip: {
        id: 'iaso.permissions.iaso_polio_vaccine_supply_chain_write_tooltip',
        defaultMessage: 'Edit and add supply chain data',
    },
    iaso_polio_notifications: {
        id: 'iaso.permissions.iaso_polio_notifications',
        defaultMessage: 'Polio notifications - Read and Write',
    },
    iaso_polio_notifications_tooltip: {
        id: 'iaso.permissions.tooltip.iaso_polio_notifications',
        defaultMessage: 'Manage polio notifications - Read and Write',
    },
    iaso_polio_vaccine_stock_management_read: {
        id: 'iaso.permissions.iaso_polio_vaccine_stock_management_read',
        defaultMessage: 'Polio vaccine stock management - Read',
    },
    iaso_polio_vaccine_stock_management_read_tooltip: {
        id: 'iaso.permissions.iaso_polio_vaccine_stock_management_read_tooltip',
        defaultMessage:
            'See summary of vaccine stock management, by country and vaccine',
    },
    iaso_polio_vaccine_stock_management_write: {
        id: 'iaso.permissions.iaso_polio_vaccine_stock_management_write',
        defaultMessage: 'Polio vaccine stock management - Write',
    },
    iaso_polio_vaccine_stock_management_write_tooltip: {
        id: 'iaso.permissions.iaso_polio_vaccine_stock_management_write_tooltip',
        defaultMessage: 'Edit and add vaccine stock management data',
    },
    iaso_polio_chronogram: {
        id: 'iaso.permissions.iaso_polio_chronogram',
        defaultMessage: 'Polio chronogram - Read and Write',
    },
    iaso_polio_chronogram_tooltip: {
        id: 'iaso.permissions.tooltip.iaso_polio_chronogram',
        defaultMessage: 'Manage polio chronogram - Read and Write',
    },
    iaso_polio_chronogram_restricted_write: {
        id: 'iaso.permissions.iaso_polio_chronogram_restricted_write',
        defaultMessage: 'Polio chronogram user - Restricted Write',
    },
    iaso_polio_chronogram_restricted_write_tooltip: {
        id: 'iaso.permissions.tooltip.iaso_polio_chronogram_restricted_write',
        defaultMessage: 'Manage polio chronogram - Restricted Write',
    },
    iaso_polio_budget_permissions: {
        id: 'iaso.permissions.readEdit.polio_budget_permissions',
        defaultMessage: 'Polio budget',
    },
    iaso_polio_budget_permissions_tooltip: {
        id: 'iaso.permissions.readEdit.tooltip.polio_budget_permissions',
        defaultMessage:
            'View budget approval process and take action as defined by your role in the process. Extra admin powers: Override any step in the process if needed.',
    },
    iaso_polio_chronogram_permissions: {
        id: 'iaso.permissions.readEdit.polio_chronogram_permissions',
        defaultMessage: 'Polio chronogram',
    },
    iaso_polio_chronogram_permissions_tooltip: {
        id: 'iaso.permissions.readEdit.tooltip.polio_chronogram_permissions',
        defaultMessage:
            'Manage polio chronogram - Read and Write - Restricted Write',
    },
    iaso_polio_vaccine_supply_chain_permissions: {
        id: 'iaso.permissions.readEdit.polio_vaccine_supply_chain_permissions',
        defaultMessage: 'Polio vaccine supply chain',
    },
    iaso_polio_vaccine_supply_chain_permissions_tooltip: {
        id: 'iaso.permissions.readEdit.tooltip.polio_vaccine_supply_chain_permissions',
        defaultMessage:
            'See summary of vaccine supply chain, by country and vaccine. Edit and add supply chain data',
    },
    iaso_polio_vaccine_stock_management_permissions: {
        id: 'iaso.permissions.readEdit.polio_vaccine_stock_management_permissions',
        defaultMessage: 'Polio vaccine stock management',
    },
    iaso_polio_vaccine_stock_management_permissions_tooltip: {
        id: 'iaso.permissions.readEdit.tooltip.polio_vaccine_stock_management_permissions',
        defaultMessage:
            'See summary of vaccine stock management, by country and vaccine. Edit and add vaccine stock management data',
    },
    iaso_polio_vaccine_authorization_permissions: {
        id: 'iaso.permissions.readEdit.polio_vaccine_authorization_permissions',
        defaultMessage: 'Polio Vaccine Authorizations',
    },
    iaso_polio_vaccine_authorization_permissions_tooltip: {
        id: 'iaso.permissions.readEdit.tooltip.polio_vaccine_authorization_permissions',
        defaultMessage:
            'Admin and no-admin permission on managing polio vaccine authorizations',
    },
    iaso_polio_vaccine_stock_earmarks_permissions: {
        id: 'iaso.permissions.readEdit.polio_vaccine_stock_earmarks_permissions',
        defaultMessage: 'Polio vaccine stock earmarks',
    },
    iaso_polio_vaccine_stock_earmarks_permissions_tooltip: {
        id: 'iaso.permissions.readEdit.tooltip.polio_vaccine_stock_earmarks_permissions',
        defaultMessage: 'Manage vaccine stock earmarks',
    },
    iaso_polio_country_plan_permissions: {
        id: 'iaso.permissions.iaso_polio_country_plan_permissions',
        defaultMessage: 'National Logistics Plan',
    },
    iaso_polio_country_plan_permissions_tooltip: {
        id: 'iaso.permissions.iaso_polio_country_plan_permissions_tooltip',
        defaultMessage:
            "Allows to manage data for vaccine module's national logistics plan",
    },
});
