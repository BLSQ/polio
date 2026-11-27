import React, { FunctionComponent } from 'react';
import Table from '@mui/material/Table/Table';
import TableBody from '@mui/material/TableBody/TableBody';
import { IntegratedCampaignRow } from './IntegratedCampaignRow';

type Props = { integratedCampaigns?: any[] };

export const IntegratedCampaignsInfo: FunctionComponent<Props> = ({
    integratedCampaigns = [],
}) => {
    return (
        <Table size="small">
            <TableBody>
                {integratedCampaigns.map(camp => (
                    <IntegratedCampaignRow
                        key={camp.obr_name}
                        campaignOption={camp}
                    />
                ))}
            </TableBody>
        </Table>
    );
};
