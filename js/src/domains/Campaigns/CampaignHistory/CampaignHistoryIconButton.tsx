import React, { FunctionComponent } from 'react';
import Box from '@mui/material/Box/Box';
import Grid from '@mui/material/Grid/Grid';
import { IconButton } from 'bluesquare-components';
import MESSAGES from '../../../constants/messages';
import { Campaign } from '../../../constants/types';
import { baseUrls } from '../../../constants/urls';
import { useStyles } from '../../../styles/theme';

type Props = { selectedCampaign?: Campaign };

export const CampaignHistoryIconButton: FunctionComponent<Props> = ({
    selectedCampaign,
}) => {
    const classes: Record<string, string> = useStyles();
    if (!selectedCampaign) return null;
    return (
        <Grid item xs={12} md={4} className={classes.historyLink}>
            <Box alignItems="center">
                <IconButton
                    url={`/${baseUrls.campaignHistory}/campaignId/${selectedCampaign?.id}`}
                    icon="history"
                    tooltipMessage={MESSAGES.campaignHistory}
                />
            </Box>
        </Grid>
    );
};
